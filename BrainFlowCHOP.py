import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from scipy.signal import resample
from pythonosc import udp_client
from numba import njit, prange
import gc
import time
import re

# Global variables
board = None
board_id = None  # Default to BrainBit board
params = BrainFlowInputParams()
osc_client = None

# Kalman filter state variables
kalman_state_estimates = None
kalman_estimate_covariances = None
last_cleanup_time = time.time()

@njit
def kalman_filter(data, process_noise, measurement_noise, state_estimate, estimate_covariance):
    if np.isnan(state_estimate) or np.isnan(estimate_covariance):
        state_estimate = 0
        estimate_covariance = 1
    # Simple Kalman filter implementation
    estimate_covariance = estimate_covariance + process_noise
    kalman_gain = estimate_covariance / (estimate_covariance + measurement_noise)
    state_estimate = state_estimate + kalman_gain * (data - state_estimate)
    estimate_covariance = (1 - kalman_gain) * estimate_covariance
    return state_estimate, estimate_covariance

def ensure_unique_name(scriptOp):
    base_name = 'brainflow'
    current_name = scriptOp.name

    if current_name.startswith(base_name):
        num_part = current_name[len(base_name):]
        if num_part.isdigit():
            return  # Name already conforms to the pattern

    # Find all CHOPs with similar names to avoid duplicates
    existing_names = {op.name for op in scriptOp.parent().children if op.name.startswith(base_name)}
    
    # Determine the next available unique name
    for i in range(1, 1000):  # Arbitrary large number to ensure we find an available name
        new_name = f"{base_name}{i}"
        if new_name not in existing_names:
            scriptOp.name = new_name
            break

def onSetupParameters(scriptOp):
    ensure_unique_name(scriptOp)
    
    # General Settings page
    general_page = scriptOp.appendCustomPage('General Settings')
    board_param = general_page.appendMenu('Board', label='Board')
    board_param[0].menuNames = [name for name, value in BoardIds.__members__.items()]
    board_param[0].menuLabels = [name for name in BoardIds.__members__.keys()]
    general_page.appendFloat('Resample', label='Re-sample Rate')
    general_page.appendStr('Serialport', label='Serial Port')

    # Time Settings page
    time_page = scriptOp.appendCustomPage('Time Settings')
    time_page.appendFloat('Updateinterval', label='Update Interval')

    # Filter Settings page
    filter_page = scriptOp.appendCustomPage('Filter Settings')
    filter_page.appendToggle('Filteractive', label='Filter Active')
    filter_page.appendFloat('Processnoise', label='Process Noise')
    filter_page.appendFloat('Measurementnoise', label='Measurement Noise')
    filter_page.appendFloat('Initialstateestimate', label='Initial State Estimate')
    filter_page.appendFloat('Initialestimatecovariance', label='Initial Estimate Covariance')

    # FFT Settings page
    fft_page = scriptOp.appendCustomPage('FFT Settings')
    fft_page.appendToggle('Fftactive', label='FFT Active')

    # OSC Settings page
    osc_page = scriptOp.appendCustomPage('OSC Settings')
    osc_page.appendStr('Oscaddress', label='OSC Address')
    osc_page.appendInt('Oscport', label='OSC Port')
    osc_page.appendStr('Oscmessage', label='OSC Message')
    osc_page.appendStr('Oscchannels', label='OSC Channels')

    # Set default values
    scriptOp.par.Board.menuIndex = 0  # Default to the first board in the menu
    scriptOp.par.Serialport.val = '/dev/tty.Bluetooth-Incoming-Port'
    scriptOp.par.Oscaddress.val = '127.0.0.1'
    scriptOp.par.Oscport.val = 6448
    scriptOp.par.Resample.val = 250
    scriptOp.par.Oscmessage.val = '/wek/inputs'
    scriptOp.par.Oscchannels.val = '*'

def onCook(scriptOp):
    ensure_unique_name(scriptOp)
    
    global board
    global params
    global osc_client
    global kalman_state_estimates
    global kalman_estimate_covariances
    global last_cleanup_time
    
    # Get selected board id
    board_name = scriptOp.par.Board.eval()
    board_id = BoardIds.__members__[board_name].value

    # Initialize the board on the first run
    if board is None:
        try:
            params.serial_port = scriptOp.par.Serialport.eval()
            board = BoardShim(board_id, params)
            board.prepare_session()
            board.start_stream()
            print(f"Data streaming started on {params.serial_port}. Collecting data...")
        except Exception as e:
            print(f"Failed to start board: {e}")
            return

    # Initialize OSC client
    if osc_client is None:
        osc_address = scriptOp.par.Oscaddress.eval()
        osc_port = scriptOp.par.Oscport.eval()
        osc_client = udp_client.SimpleUDPClient(osc_address, osc_port)
        print(f"OSC Client started at {osc_address}:{osc_port}")

    # Get update interval
    update_interval = scriptOp.par.Updateinterval.eval()

    try:
        # Collect data (no need to wait for update_interval in this example)
        data = board.get_current_board_data(250)  # Get 250 sample data
        
        # Convert data to numpy array
        eeg_channels = BoardShim.get_eeg_channels(board_id)
        eeg_data = data[eeg_channels, :]
        
        # If data is empty
        if eeg_data.size == 0:
            print("No EEG data received.")
            return
        
        # Get Filter Settings parameters
        filter_active = scriptOp.par.Filteractive.eval()
        process_noise = scriptOp.par.Processnoise.eval()
        measurement_noise = scriptOp.par.Measurementnoise.eval()
        initial_state_estimate = scriptOp.par.Initialstateestimate.eval()
        initial_estimate_covariance = scriptOp.par.Initialestimatecovariance.eval()

        # Initialize Kalman filter parameters
        if kalman_state_estimates is None:
            num_channels = eeg_data.shape[0]
            kalman_state_estimates = np.full(num_channels, initial_state_estimate)
            kalman_estimate_covariances = np.full(num_channels, initial_estimate_covariance)

        # Apply Kalman filter if active
        if filter_active:
            for i in prange(eeg_data.shape[0]):
                for j in range(eeg_data.shape[1]):
                    kalman_state_estimates[i], kalman_estimate_covariances[i] = kalman_filter(
                        eeg_data[i, j], 
                        process_noise, 
                        measurement_noise, 
                        kalman_state_estimates[i], 
                        kalman_estimate_covariances[i]
                    )
                    eeg_data[i, j] = kalman_state_estimates[i]
        
        # Get General Settings parameters
        resample_rate = scriptOp.par.Resample.eval()

        # Resample data
        num_channels = eeg_data.shape[0]
        eeg_data_resampled = resample(eeg_data, int(resample_rate), axis=1)
        num_samples = eeg_data_resampled.shape[1]

        # Get FFT Settings parameters
        fft_active = scriptOp.par.Fftactive.eval()

        # Apply FFT if active
        if fft_active:
            fft_data = np.abs(np.fft.fft(eeg_data_resampled, axis=1))
            fft_num_samples = fft_data.shape[1]  # Use this length for fft data
            fft_data = fft_data[:, :fft_num_samples]  # Take the positive frequency part

        # Clear the script CHOP before writing data
        scriptOp.clear()

        # Write data to script CHOP
        for chan in range(num_channels):
            scriptOp.appendChan(f'chan{chan+1}')

        if fft_active:
            for chan in range(num_channels):
                scriptOp.appendChan(f'fft_chan{chan+1}')

        scriptOp.numSamples = num_samples
        
        for chan in range(num_channels):
            for sample in range(num_samples):
                scriptOp[chan][sample] = eeg_data_resampled[chan, sample]

        if fft_active:
            for chan in range(num_channels):
                for sample in range(fft_num_samples):
                    scriptOp[num_channels + chan][sample] = fft_data[chan, sample]

        # Get OSC message address
        osc_message = scriptOp.par.Oscmessage.eval()
        
        # Get OSC channels to send
        osc_channels = scriptOp.par.Oscchannels.eval()
        total_channels = num_channels + (num_channels if fft_active else 0)
        
        if osc_channels == '*':
            channels_to_send = list(range(total_channels))
        else:
            channels_to_send = []
            for chan in osc_channels.split():
                chan = chan.strip()
                if chan.startswith('chan'):
                    chan_index = int(chan[4:]) - 1
                    if 0 <= chan_index < num_channels:
                        channels_to_send.append(chan_index)
                elif chan.startswith('fft_chan'):
                    chan_index = int(chan[8:]) - 1
                    if 0 <= chan_index < num_channels:
                        channels_to_send.append(num_channels + chan_index)

        # Send data to Wekinator
        for sample_idx in range(min(num_samples, fft_num_samples if fft_active else num_samples)):
            message = []
            for chan in channels_to_send:
                if chan < num_channels:
                    message.append(eeg_data_resampled[chan, sample_idx])
                elif fft_active:
                    fft_chan = chan - num_channels
                    if fft_chan < num_channels:
                        message.append(fft_data[fft_chan, sample_idx])
            osc_client.send_message(osc_message, message)

        # Perform cleanup at regular intervals
        current_time = time.time()
        if current_time - last_cleanup_time > 60:  # Perform cleanup every 60 seconds
            print("Performing cleanup...")
            gc.collect()  # Run garbage collector
            last_cleanup_time = current_time

    except Exception as e:
        print(f"Data stream error: {e}")
        
    finally:
        # No need to close the session, it will stay open
        pass
