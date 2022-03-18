import tkinter as tk
import time
from datetime import datetime
import matplotlib as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)


class TradingInterface:
    def __init__(self, strategy):
        self.trading_strategy = strategy
        self.window = tk.Tk()
        self.window.title("Trading Strategy")
        self.trade_frame = tk.Frame(width=20)
        self.trade_frame.grid(row=1, column=0)
        self.tweet_frame = tk.Frame()
        self.tweet_frame.grid(row=1, column=1)
        self.metrics_frame = tk.Frame()
        self.metrics_frame.grid(row=2, column=0)
        self.plot_frame = tk.Frame()
        self.plot_frame.grid(row=2, column=1)

        trade_header = tk.Frame()
        trade_header.grid(row=0, column=0)
        tk.Label(trade_header, text=f"Recent Trades", font='Helvetica 18 bold').pack()

        twitter_header = tk.Frame()
        twitter_header.grid(row=0, column=1)
        tk.Label(twitter_header, text=f"Recent Tweets", font='Helvetica 18 bold').pack()
        self.window.grid_rowconfigure(0, minsize=50, weight=1)
        self.window.grid_rowconfigure(1, minsize=200, weight=1)
        self.window.grid_columnconfigure(0, minsize=800, weight=1)
        self.window.grid_columnconfigure(1, minsize=800, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.after(500, self.listen_for_input)
        self.window.mainloop()

    def listen_for_input(self):
        if not self.trading_strategy.is_on:
            self.window.destroy()
        if self.trading_strategy.check_new_data():
            self.update_trading_window()
            self.update_tweet_window()
            self.update_plot()
            self.update_metrics_frame()
        self.window.after(500, self.listen_for_input)

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def print_list(self, frame, text_list):
        for text in text_list:
            label = tk.Label(frame, text=text)
            label.pack()

    def update_trading_window(self):
        self.clear_frame(self.trade_frame)
        self.print_list(self.trade_frame, self.trading_strategy.recent_trades)

    def update_tweet_window(self):
        self.clear_frame(self.tweet_frame)
        self.print_list(self.tweet_frame, self.trading_strategy.recent_tweets)

    def update_plot(self):
        if len(self.trading_strategy.small_window_avg) == 0:
            return
        self.clear_frame(self.plot_frame)
        fig = Figure(figsize=(8, 5), dpi=100)

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the graph
        plot1.plot(self.trading_strategy.small_window_avg, 'blue', label='10 tweet moving avg')
        plot1.plot(self.trading_strategy.large_window_avg, 'r', label='20 tweet moving avg')
        plot1.plot(self.trading_strategy.small_window_avg)
        plot1.set_title("Sentiment Moving Average")
        plot1.legend(loc='upper right')
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def update_metrics_frame(self):
        self.clear_frame(self.metrics_frame)
        font = 'Helvetica 15 bold'
        if len(self.trading_strategy.large_window_avg)>0:
            tk.Label(self.metrics_frame, text=f"Large Window Avg: {self.trading_strategy.large_window_avg[-1]:5.2f}", font=font).pack()
            tk.Label(self.metrics_frame, text=f"Small Window Avg: {self.trading_strategy.small_window_avg[-1]:5.2f}", font=font).pack()

        strategy_signal = {2:'Strong Buy', 1:'Weak Buy', 0:'None', -1:'Weak Sell', -2:'Strong Sell'}
        tk.Label(self.metrics_frame, text=f"Signal: {strategy_signal[self.trading_strategy.signal]}", font=font).pack()
        tk.Label(self.metrics_frame, text=f"Target Position: {self.trading_strategy.target:5.2f}", font=font).pack()

