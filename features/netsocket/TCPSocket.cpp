/* Socket
 * Copyright (c) 2015 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "TCPSocket.h"
#include "Timer.h"
#include "mbed_assert.h"

#define READ_FLAG           0x1u
#define WRITE_FLAG          0x2u

#define TCP_BYTE_TRACK_DEBUG 0

std::map<TCPSocket*, uint32_t> TCPSocket::tcp_socket_to_bytes_sent;
std::map<TCPSocket*, uint32_t> TCPSocket::tcp_socket_to_bytes_recv;

uint32_t TCPSocket::get_tcp_bytes_sent(void) {
    uint32_t sum = 0;
    #if TCP_BYTE_TRACK_DEBUG
    printf("____get_tcp_bytes_sent____\r\n");
    #endif
    for(std::map<TCPSocket*, uint32_t>::iterator it = tcp_socket_to_bytes_sent.begin(); it != tcp_socket_to_bytes_sent.end(); ++it) {
        //printf("TCP Socket: %x sent: %d bytes\r\n", it->first, it->second);
        sum += it->second;
    }

    //printf("TCP Bytes sent sum: %d\r\n", sum);
    return sum;
}

uint32_t TCPSocket::get_tcp_bytes_received(void) {
    uint32_t sum = 0;
    #if TCP_BYTE_TRACK_DEBUG
    printf("____get_tcp_bytes_recv____\r\n");
    #endif
    for(std::map<TCPSocket*, uint32_t>::iterator it = tcp_socket_to_bytes_recv.begin(); it != tcp_socket_to_bytes_recv.end(); ++it) {
        //printf("TCP Socket: %x received: %u bytes\r\n", it->first, it->second);
        sum += it->second;
    }

    //printf("TCP Bytes recv sum: %d\r\n", sum);
    return sum;
}


TCPSocket::TCPSocket()
    : _pending(0), _event_flag(),
      _read_in_progress(false), _write_in_progress(false)
{
}

TCPSocket::~TCPSocket()
{
    close();
}

nsapi_protocol_t TCPSocket::get_proto()
{
    return NSAPI_TCP;
}

nsapi_error_t TCPSocket::connect(const SocketAddress &address)
{
    _lock.lock();
    nsapi_error_t ret;

    // If this assert is hit then there are two threads
    // performing a send at the same time which is undefined
    // behavior
    MBED_ASSERT(!_write_in_progress);
    _write_in_progress = true;

    bool blocking_connect_in_progress = false;

    while (true) {
        if (!_socket) {
            ret = NSAPI_ERROR_NO_SOCKET;
            break;
        }

        _pending = 0;
        ret = _stack->socket_connect(_socket, address);
        if ((_timeout == 0) || !(ret == NSAPI_ERROR_IN_PROGRESS || ret == NSAPI_ERROR_ALREADY)) {
            break;
        } else {
            blocking_connect_in_progress = true;

            uint32_t flag;

            // Release lock before blocking so other threads
            // accessing this object aren't blocked
            _lock.unlock();
            flag = _event_flag.wait_any(WRITE_FLAG, _timeout);
            _lock.lock();
            if (flag & osFlagsError) {
                // Timeout break
                break;
            }
        }
    }

    _write_in_progress = false;

    /* Non-blocking connect gives "EISCONN" once done - convert to OK for blocking mode if we became connected during this call */
    if (ret == NSAPI_ERROR_IS_CONNECTED && blocking_connect_in_progress) {
        ret = NSAPI_ERROR_OK;
    }

    _lock.unlock();
    return ret;
}

nsapi_error_t TCPSocket::connect(const char *host, uint16_t port)
{
    SocketAddress address;
    nsapi_error_t err = _stack->gethostbyname(host, &address);
    if (err) {
        return NSAPI_ERROR_DNS_FAILURE;
    }

    address.set_port(port);

    // connect is thread safe
    return connect(address);
}

nsapi_size_or_error_t TCPSocket::send(const void *data, nsapi_size_t size)
{
    _lock.lock();
    const uint8_t *data_ptr = static_cast<const uint8_t *>(data);
    nsapi_size_or_error_t ret;
    nsapi_size_t written = 0;

    // If this assert is hit then there are two threads
    // performing a send at the same time which is undefined
    // behavior
    MBED_ASSERT(!_write_in_progress);
    _write_in_progress = true;

    // Unlike recv, we should write the whole thing if blocking. POSIX only
    // allows partial as a side-effect of signal handling; it normally tries to
    // write everything if blocking. Without signals we can always write all.
    while (true) {
        if (!_socket) {
            ret = NSAPI_ERROR_NO_SOCKET;
            break;
        }

        _pending = 0;
        ret = _stack->socket_send(_socket, data_ptr + written, size - written);
        if (ret >= 0) {
            written += ret;
            if (written >= size) {
                break;
            }
        }
        if (_timeout == 0) {
            break;
        } else if (ret == NSAPI_ERROR_WOULD_BLOCK) {
            uint32_t flag;

            // Release lock before blocking so other threads
            // accessing this object aren't blocked
            _lock.unlock();
            flag = _event_flag.wait_any(WRITE_FLAG, _timeout);
            _lock.lock();

            if (flag & osFlagsError) {
                // Timeout break
                break;
            }
        } else if (ret < 0) {
            break;
        }
    }

    _write_in_progress = false;
    _lock.unlock();
    if (ret <= 0 && ret != NSAPI_ERROR_WOULD_BLOCK) {
        return ret;
    } else if (written == 0) {
        return NSAPI_ERROR_WOULD_BLOCK;
    } else {
        if (written > 0)
            tcp_socket_to_bytes_sent[this] += written;
        //printf("Returning bytes sent: %d\r\n", written);
        return written;
    }
}

nsapi_size_or_error_t TCPSocket::recv(void *data, nsapi_size_t size)
{
    _lock.lock();
    nsapi_size_or_error_t ret;

    // If this assert is hit then there are two threads
    // performing a recv at the same time which is undefined
    // behavior
    MBED_ASSERT(!_read_in_progress);
    _read_in_progress = true;

    while (true) {
        if (!_socket) {
            ret = NSAPI_ERROR_NO_SOCKET;
            break;
        }

        _pending = 0;
        ret = _stack->socket_recv(_socket, data, size);
        if ((_timeout == 0) || (ret != NSAPI_ERROR_WOULD_BLOCK)) {
            if(ret > 0)
                tcp_socket_to_bytes_recv[this] += ret;
            break;
        } else {
            uint32_t flag;

            // Release lock before blocking so other threads
            // accessing this object aren't blocked
            _lock.unlock();
            flag = _event_flag.wait_any(READ_FLAG, _timeout);
            _lock.lock();

            if (flag & osFlagsError) {
                // Timeout break
                ret = NSAPI_ERROR_WOULD_BLOCK;
                break;
            }
        }
    }

    _read_in_progress = false;
    _lock.unlock();

    return ret;
}

void TCPSocket::event()
{
    _event_flag.set(READ_FLAG|WRITE_FLAG);

    _pending += 1;
    if (_callback && _pending == 1) {
        _callback();
    }
}
