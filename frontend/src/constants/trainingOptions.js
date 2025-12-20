export const TRAINING_OPTIMIZERS = ["Adam", "SGD"];
export const TRAINING_LOSS_FUNCTIONS = ["crossentropy"];

export const VALIDATION_SPLITS = [
  { label: "10%", value: 0.1 },
  { label: "15%", value: 0.15 },
  { label: "20%", value: 0.2 },
  { label: "25%", value: 0.25 },
  { label: "30%", value: 0.3 },
];

export const DEFAULT_TRAINING_CONFIG = {
  epochs_num: "10",
  batch_size: "32",
  learning_rate: "0.001",
  optimizer: TRAINING_OPTIMIZERS[0],
  loss_function: TRAINING_LOSS_FUNCTIONS[0],
  val_split: 0.2,
};
