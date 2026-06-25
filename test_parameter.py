TEST_N_AGENTS = 8

NODE_INPUT_DIM = 5
OTHER_INFO_INPUT_DIM = 3
EMBEDDING_DIM = 64
MESSAGE_BYTES = EMBEDDING_DIM * 4

COMM_MODE = "event"  # "always", "fixed", "event", "random"
COMM_THRESHOLD = 0.2
COMM_INTERVAL = 4
COMM_PROB = 0.5

K_SIZE = 25  # the number of neighbors

USE_GPU = True  # do you want to use GPUS?
NUM_GPU = 1
NUM_META_AGENT = 24  # the number of processes
FOLDER_NAME = 'event_tau_02'
model_path = f'model/{FOLDER_NAME}'
gifs_path = f'results/{FOLDER_NAME}/gifs'

NUM_TEST = 100
NUM_RUN = 1
SAVE_GIFS = False  # do you want to save GIFs
