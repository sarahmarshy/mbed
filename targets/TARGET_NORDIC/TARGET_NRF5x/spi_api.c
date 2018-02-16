#include "spi_api.h"
#include "nrf_drv_spi.h"
#include "nrf_drv_spis.h"
#include "nrf_drv_common.h"

#if DEVICE_SPI

#define SPI_INSTANCE_COUNT 3
#define INSTANCE_ID 0

/** Initialize the SPI peripheral
 *
 * Configures the pins used by SPI, sets a default format and frequency, and enables the peripheral
 * @param[out] obj  The SPI object to initialize
 * @param[in]  mosi The pin to use for MOSI
 * @param[in]  miso The pin to use for MISO
 * @param[in]  sclk The pin to use for SCLK
 * @param[in]  ssel The pin to use for SSEL
 */
void spi_init(spi_t *obj, PinName mosi, PinName miso, PinName sclk, PinName ssel)
{
    struct spi_s *spi_inst = obj;
 
    nrf_drv_spi_config_t config = NRF_DRV_SPI_DEFAULT_CONFIG;
    config.sck_pin = sclk;
    config.mosi_pin = mosi;
    config.miso_pin = miso;
    config.ss_pin = ssel; 
    memcpy(&(spi_inst->config), &config, sizeof(nrf_drv_spi_config_t));
    /* TODO: use pin configuration to choose instance instead of hard coded value */
    int instance = 0;
    nrf_drv_spi_t spi_drv_inst = NRF_DRV_SPI_INSTANCE(0);
    memcpy(&(spi_inst->spi_drv_inst), &spi_drv_inst, sizeof(nrf_drv_spi_t)); 
    uint32_t err = nrf_drv_spi_init(&(spi_inst->spi_drv_inst), &(spi_inst->config), NULL, NULL); 
    
}

/** Release a SPI object
 *
 * TODO: spi_free is currently unimplemented
 * This will require reference counting at the C++ level to be safe
 *
 * Return the pins owned by the SPI object to their reset state
 * Disable the SPI peripheral
 * Disable the SPI clock
 * @param[in] obj The SPI object to deinitialize
 */
void spi_free(spi_t *obj)
{
    struct spi_s *spi_inst = obj;
    nrf_drv_spi_uninit(&(spi_inst->spi_drv_inst)); 
}

/** Configure the SPI format
 *
 * Set the number of bits per frame, configure clock polarity and phase, shift order and master/slave mode.
 * The default bit order is MSB.
 * @param[in,out] obj   The SPI object to configure
 * @param[in]     bits  The number of bits per frame
 * @param[in]     mode  The SPI mode (clock polarity, phase, and shift direction)
 * @param[in]     slave Zero for master mode or non-zero for slave mode
 */
void spi_format(spi_t *obj, int bits, int mode, int slave)
{
    struct spi_s *spi_inst = obj;
    nrf_drv_spi_config_t *config = &(spi_inst->config);
    if(mode == 0)
        config->mode = NRF_DRV_SPI_MODE_0;
    else if(mode == 1)
        config->mode = NRF_DRV_SPI_MODE_1;
    else if(mode == 2)
        config->mode = NRF_DRV_SPI_MODE_2;
    else if(mode == 3)
        config->mode = NRF_DRV_SPI_MODE_3;

    //TODO: bits???
}
         

/** Set the SPI baud rate
 *
 * Actual frequency may differ from the desired frequency due to available dividers and bus clock
 * Configures the SPI peripheral's baud rate
 * @param[in,out] obj The SPI object to configure
 * @param[in]     hz  The baud rate in Hz
 */
void spi_frequency(spi_t *obj, int hz)
{
    struct spi_s *spi_inst = obj;
    nrf_drv_spi_config_t *config = &(spi_inst->config);
    nrf_drv_spi_frequency_t new_freq;
    if (hz < 250000) {
        new_freq = NRF_DRV_SPI_FREQ_125K;
    } else if (hz < 500000) {
        new_freq = NRF_DRV_SPI_FREQ_250K;
    } else if (hz < 1000000) {
        new_freq = NRF_DRV_SPI_FREQ_500K;
    } else if (hz < 2000000) {
        new_freq = NRF_DRV_SPI_FREQ_1M;
    } else if (hz < 4000000) {
        new_freq = NRF_DRV_SPI_FREQ_2M;
    } else if (hz < 800000) {
        new_freq = NRF_DRV_SPI_FREQ_4M;
    } else {
        new_freq = NRF_DRV_SPI_FREQ_8M;
    }
    config->frequency = new_freq;
}
         

/**@}*/
/**
 * \defgroup SynchSPI Synchronous SPI Hardware Abstraction Layer
 * @{
 */

/** Write a byte out in master mode and receive a value
 *
 * @param[in] obj   The SPI peripheral to use for sending
 * @param[in] value The value to send
 * @return Returns the value received during send
 */
int  spi_master_write(spi_t *obj, int value)
{
    struct spi_s *spi_obj = obj;
    const uint8_t tx_buff[1] = {(uint8_t) value};
    uint8_t rx_buff[1];
    nrf_drv_spi_transfer(&(spi_obj->spi_drv_inst), tx_buff, 1, rx_buff, 1);
    return rx_buff[0];
}
/** Write a block out in master mode and receive a value
 *
 *  The total number of bytes sent and recieved will be the maximum of
 *  tx_length and rx_length. The bytes written will be padded with the
 *  value 0xff.
 *
 * @param[in] obj        The SPI peripheral to use for sending
 * @param[in] tx_buffer  Pointer to the byte-array of data to write to the device
 * @param[in] tx_length  Number of bytes to write, may be zero
 * @param[in] rx_buffer  Pointer to the byte-array of data to read from the device
 * @param[in] rx_length  Number of bytes to read, may be zero
 * @param[in] write_fill Default data transmitted while performing a read
 * @returns
 *      The number of bytes written and read from the device. This is
 *      maximum of tx_length and rx_length.
 */
int spi_master_block_write(spi_t *obj, const char *tx_buffer, int tx_length, char *rx_buffer, int rx_length, char write_fill)
{
    struct spi_s *spi_obj = obj;
    nrf_drv_spi_transfer(&(spi_obj->spi_drv_inst), (const uint8_t *) tx_buffer, tx_length, (uint8_t *) rx_buffer, rx_length);
    int max = rx_length < tx_length ? tx_length : rx_length;
    return max; 
} 

/** Check if a value is available to read
 *
 * @param[in] obj The SPI peripheral to check
 * @return non-zero if a value is available
 */
int  spi_slave_receive(spi_t *obj);

/** Get a received value out of the SPI receive buffer in slave mode
 *
 * Blocks until a value is available
 * @param[in] obj The SPI peripheral to read
 * @return The value received
 */
int  spi_slave_read(spi_t *obj);

/** Write a value to the SPI peripheral in slave mode
 *
 * Blocks until the SPI peripheral can be written to
 * @param[in] obj   The SPI peripheral to write
 * @param[in] value The value to write
 */
void spi_slave_write(spi_t *obj, int value);

/** Checks if the specified SPI peripheral is in use
 *
 * @param[in] obj The SPI peripheral to check
 * @return non-zero if the peripheral is currently transmitting
 */
int  spi_busy(spi_t *obj);

/** Get the module number
 *
 * @param[in] obj The SPI peripheral to check
 * @return The module number
 */
uint8_t spi_get_module(spi_t *obj);

/**@}*/

#if DEVICE_SPI_ASYNCH
/**
 * \defgroup AsynchSPI Asynchronous SPI Hardware Abstraction Layer
 * @{
 */

/** Begin the SPI transfer. Buffer pointers and lengths are specified in tx_buff and rx_buff
 *
 * @param[in] obj       The SPI object that holds the transfer information
 * @param[in] tx        The transmit buffer
 * @param[in] tx_length The number of bytes to transmit
 * @param[in] rx        The receive buffer
 * @param[in] rx_length The number of bytes to receive
 * @param[in] bit_width The bit width of buffer words
 * @param[in] event     The logical OR of events to be registered
 * @param[in] handler   SPI interrupt handler
 * @param[in] hint      A suggestion for how to use DMA with this transfer
 */
void spi_master_transfer(spi_t *obj, const void *tx, size_t tx_length, void *rx, size_t rx_length, uint8_t bit_width, uint32_t handler, uint32_t event, DMAUsage hint);

/** The asynchronous IRQ handler
 *
 * Reads the received values out of the RX FIFO, writes values into the TX FIFO and checks for transfer termination
 * conditions, such as buffer overflows or transfer complete.
 * @param[in] obj     The SPI object that holds the transfer information
 * @return Event flags if a transfer termination condition was met; otherwise 0.
 */
uint32_t spi_irq_handler_asynch(spi_t *obj);

/** Attempts to determine if the SPI peripheral is already in use
 *
 * If a temporary DMA channel has been allocated, peripheral is in use.
 * If a permanent DMA channel has been allocated, check if the DMA channel is in use.  If not, proceed as though no DMA
 * channel were allocated.
 * If no DMA channel is allocated, check whether tx and rx buffers have been assigned.  For each assigned buffer, check
 * if the corresponding buffer position is less than the buffer length.  If buffers do not indicate activity, check if
 * there are any bytes in the FIFOs.
 * @param[in] obj The SPI object to check for activity
 * @return Non-zero if the SPI port is active or zero if it is not.
 */
uint8_t spi_active(spi_t *obj);

/** Abort an SPI transfer
 *
 * @param obj The SPI peripheral to stop
 */
void spi_abort_asynch(spi_t *obj);

#endif // DEVICE_SPI_ASYNCH

#endif // DEVICE_SPI
