import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import threading
import tkinter as tk
from tkinter import ttk
from queue import Queue
 
 
# Load a real-world dataset
df = px.data.gapminder()
 
 
# Shared state using queues
state_queue = Queue()
 
 
# Initialize the Dash app
app = dash.Dash(__name__)
 
 
# Layout for the Dash app
app.layout = html.Div([
   dcc.Dropdown(
       id='continent-dropdown',
       options=[{'label': continent, 'value': continent} for continent in df['continent'].unique()],
       value='Asia',
       style={'width': '50%'}
   ),
   dcc.Checklist(
       id='year-checklist',
       options=[{'label': str(year), 'value': year} for year in df['year'].unique()],
       value=[1952],
       style={'margin': '20px 0'}
   ),
   dcc.Slider(
       id='pop-slider',
       min=df['pop'].min(),
       max=df['pop'].max(),
       value=df['pop'].min(),
       marks={int(pop): f'{int(pop / 1e6)}M' for pop in df['pop'].unique()},
       step=1e7,
       tooltip={"placement": "bottom", "always_visible": True}
   ),
   dcc.RadioItems(
       id='chart-type',
       options=[
           {'label': 'Scatter Plot', 'value': 'scatter'},
           {'label': 'Bar Graph', 'value': 'bar'}
       ],
       value='scatter',
       labelStyle={'display': 'inline-block', 'margin': '10px'}
   ),
   html.Div(id='charts-container')
])
 
 
# Function to update the charts
def update_charts(selected_continent, selected_years, min_pop, chart_type):
   filtered_df = df[
       (df['continent'] == selected_continent) & (df['year'].isin(selected_years)) & (df['pop'] >= min_pop)]
 
 
   if chart_type == 'scatter':
       fig = px.scatter(filtered_df, x='gdpPercap', y='lifeExp', size='pop', color='country', hover_name='country',
                        title=f'Life Expectancy vs GDP per Capita in {selected_continent}', log_x=True)
   elif chart_type == 'bar':
       fig = px.bar(filtered_df, x='country', y='lifeExp', color='country',
                    title=f'Life Expectancy in {selected_continent}')
 
 
   return [dcc.Graph(figure=fig)]
 
 
# Callback to update the charts based on selections
@app.callback(
   Output('charts-container', 'children'),
   [Input('continent-dropdown', 'value'),
    Input('year-checklist', 'value'),
    Input('pop-slider', 'value'),
    Input('chart-type', 'value')]
)
def display_charts(selected_continent, selected_years, min_pop, chart_type):
   return update_charts(selected_continent, selected_years, min_pop, chart_type)
 
 
# Function to run the Dash server
def run_dash():
   app.run_server(debug=True, use_reloader=False)
 
 
# Tkinter Application Setup
def start_tkinter():
   root = tk.Tk()
   root.title("Dash Controller - The Pycodes")
   root.geometry("350x550")
 
 
   # Tkinter UI Components
   continent_var = tk.StringVar(value="Asia")
   continent_label = tk.Label(root, text="Select Continent:")
   continent_label.pack(pady=5)
   continent_dropdown = ttk.Combobox(root, textvariable=continent_var, values=df['continent'].unique(),
                                     state='readonly')
   continent_dropdown.pack(pady=5)
 
 
   year_label = tk.Label(root, text="Select Years:")
   year_label.pack(pady=5)
   year_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
   for year in df['year'].unique():
       year_listbox.insert(tk.END, year)
   year_listbox.pack(pady=5)
 
 
   pop_label = tk.Label(root, text="Minimum Population (Millions):")
   pop_label.pack(pady=5)
   pop_scale = tk.Scale(root, from_=df['pop'].min() / 1e6, to=df['pop'].max() / 1e6, orient=tk.HORIZONTAL)
   pop_scale.pack(pady=5)
 
 
   chart_type_var = tk.StringVar(value="scatter")
   chart_type_label = tk.Label(root, text="Select Chart Type:")
   chart_type_label.pack(pady=5)
   chart_type_dropdown = ttk.Combobox(root, textvariable=chart_type_var, values=["scatter", "bar"], state='readonly')
   chart_type_dropdown.pack(pady=5)
 
 
   # Advanced Buttons and Features
   def update_and_send_state():
       selected_continent = continent_var.get()
       selected_years = [int(year_listbox.get(i)) for i in year_listbox.curselection()]
       min_pop = pop_scale.get() * 1e6
       chart_type = chart_type_var.get()
 
 
       # Send state to Dash app via queue
       state_queue.put((selected_continent, selected_years, min_pop, chart_type))
 
 
       # Dynamically update Dash layout (thread-safe)
       app.layout.children[0].value = selected_continent
       app.layout.children[1].value = selected_years
       app.layout.children[2].value = min_pop
       app.layout.children[3].value = chart_type
 
 
   update_button = tk.Button(root, text="Update Dash App", command=update_and_send_state)
   update_button.pack(pady=10)
 
 
   start_button = tk.Button(root, text="Start Dash App", command=lambda: threading.Thread(target=run_dash).start())
   start_button.pack(pady=10)
 
 
   root.mainloop()
 
 
# Background thread to sync states between Tkinter and Dash
def sync_states():
   while True:
       if not state_queue.empty():
           state = state_queue.get()
           continent, years, min_pop, chart_type = state
           display_charts(continent, years, min_pop, chart_type)
 
 
# Start the Tkinter app and synchronization thread
if __name__ == "__main__":
   threading.Thread(target=start_tkinter).start()
   threading.Thread(target=sync_states, daemon=True).start()
