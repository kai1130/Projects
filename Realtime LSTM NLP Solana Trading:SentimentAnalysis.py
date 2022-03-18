import keras.models
import pandas as pd
from sklearn.model_selection import train_test_split
from keras import Sequential
from keras.layers import Embedding, LSTM, Dense
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
import matplotlib.pyplot as plt
import pickle

MODEL_PATH = r"./"
NUM_WORDS = 500

class NoDataError(Exception):
    pass

class SentimentAnalysisSystem:
    def __init__(self, file, model_path=None, tokenizer_path=None):
        self.df = None
        self.X = None
        self.y = None
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None
        self.tokenizer = None
        self.model = None

        if tokenizer_path:
            self.tokenizer = self.load_tokenizer(tokenizer_path)

        if model_path:
            self.model = self.load_model(model_path)

        if file:
            self.load_data_file(file)

    def load_data_file(self, file):
        self.df = pd.read_csv(file)
        self.df = self.df[self.df['return'].notna()]
        self.df = self.df.sort_values(['Time'])
        if self.tokenizer is None:
            self.create_tokenizer(self.df)
        self.X = self.transform_text(self.df)
        self.y = self.df['return']

    # Output: model fit history
    def fit_model(self):
        if not all([self.X_train, self.X_test, self.y_train, self.y_test]):
            self.create_train_test_split()
        return self.model.fit(self.X_train, self.y_train,
                              validation_data=(self.X_test, self.y_test), epochs=5, verbose=2)

    # Converts words into tokens and standardizes length for input into keras model
    def create_tokenizer(self, text_df):
        if text_df is None:
            raise NoDataError
        self.tokenizer = Tokenizer(num_words=NUM_WORDS, lower=True, split=' ')
        self.tokenizer.fit_on_texts(text_df['Text'].values)

    def transform_text(self, text_df):
        X = self.tokenizer.texts_to_sequences(text_df['Text'].values)
        X = pad_sequences(X, maxlen=80)
        return X

    def create_train_test_split(self):
        # Split train/test data by time to avoid data leakage
        train_split = int(0.8 * len(self.X))
        self.X_train = self.X[:train_split]
        self.X_test = self.X[train_split:]
        self.y_train = self.y[:train_split]
        self.y_test = self.y[train_split:]

    def predict(self, text):
        text_df = pd.DataFrame(data={'Text': [text]})
        X = self.transform_text(text_df)
        return self.model.predict(X).flatten()[0]

    # Creates and compiles LSTM neural network model
    def create_model(self, embed_dim=240, lstm_out=40):
        self.model = Sequential()
        self.model.add(Embedding(NUM_WORDS, embed_dim, input_length=self.X.shape[1]))
        self.model.add(LSTM(lstm_out, dropout=0.25))
        self.model.add(Dense(1, activation='linear'))
        self.model.compile(loss='mse', optimizer='adam')

    # Prints summary of model predictions, actual values, and errors
    def test_model(self):
        pred_y = self.model.predict(self.X_test).flatten()
        errors = pred_y - self.y_test
        print(pd.DataFrame(pred_y, columns=["Predicted"]).describe())
        print("Actual\n", pd.DataFrame(self.y_test).describe())
        print("Errors\n", pd.DataFrame(errors).describe())

    def top_tweets(self):
        self.df['Predicted'] = self.model.predict(self.X).flatten()
        self.df.to_csv(r"./test.csv")
        return self.df[['Text', 'Predicted']].sort_values('Predicted')

    def save_model(self, path):
        self.model.save(path)

    def load_model(self, path):
        return keras.models.load_model(path)

    def save_tokenizer(self, path):
        with open(path, 'wb') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_tokenizer(self, path):
        with open(path, 'rb') as handle:
            return pickle.load(handle)


def plot_history(train_history):
    loss = train_history.history['loss']
    val_loss = train_history.history['val_loss']
    plt.plot(loss)
    plt.plot(val_loss)
    plt.legend(['loss', 'val_loss'])
    plt.show()


if __name__ == '__main__':
    input_file = r"./combined_all_data.csv"
    sas = SentimentAnalysisSystem(input_file)
    sas.create_model()
    train_history = sas.fit_model()
    sas.test_model()
    print(sas.top_tweets())
    sas.save_model(MODEL_PATH)
    sas.save_tokenizer(r"./tokenizer.pickle")
