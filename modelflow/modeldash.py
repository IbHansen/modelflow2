import dash_interactive_graphviz
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

import pandas as pd
import webbrowser
from threading import Timer
import json

from pathlib import Path

from modelclass import model 


app = dash.Dash(__name__)

initial_dot_source = """
digraph  {
node[style="filled"]
a ->b->d
a->c->d
}
"""
smallmodel      = '''
frml <> a = c + b $ 
frml <> d1 = x + 3 * a(-1)+ c **2 +a  $ 
frml <> d3 = x + 3 * a(-1)+c **3 $  
Frml <> x = 0.5 * c +a$'''
des = {'A':'Bruttonationalprodukt i faste  priser',
       'X': 'Eksport <æøåÆØÅ>;',
       'C': 'Forbrug'}
mmodel = model(smallmodel,var_description=des,svg=1,browser=1)
df = pd.DataFrame({'X' : [0.2,0.2] , 'C' :[0.,0.] , 'R':[1.,0.4] , 'P':[0.,0.4]})
df2 = pd.DataFrame({'X' : [0.2,0.2] , 'C' :[10.,10.] , 'R':[1.,0.4] , 'P':[0.,0.4]})

xx = mmodel(df)
yy = mmodel(df2)
initial_dot_source =     mmodel.drawmodel(svg=1,all=True,browser=0,pdf=0,des=True,dot=True)

app.layout = html.Div(
    [
        html.Div(
            dash_interactive_graphviz.DashInteractiveGraphviz(id="gv",engine='dot'),
            style=dict(flexGrow=1, position="relative"),
        ),
        html.Div(
            [
               
                html.H3("var"),
                dcc.Dropdown(id='var',value=sorted(mmodel.allvar.keys())[0],options=[
                        dict(label=v, value=v)
                        for v in sorted(mmodel.allvar.keys())],
                )
                 ,
                html.H3("Up"),
                dcc.Dropdown(id="up",value="1",options=[
                        dict(label=engine, value=engine)
                        for engine in list(range(10))],
                ),
                html.H3("Downxxyyy"),
                dcc.Dropdown(id="down",value="1",options=[
                        dict(label=engine, value=engine)
                        for engine in list(range(10))],
                )
            ],
            style=dict(display="flex", flexDirection="column"),
        ),
    ],
    style=dict(position="absolute", height="100%", width="100%", display="flex"),
)


@app.callback(
    [Output("gv", "dot_source"),Output('var', "value")],
    [
     Input('var', "value"),Input('gv', "selected_node"),Input('up', "value"),
     Input('down', "value")],
)
def display_output( var,select_var,up,down):
    # value=mmodel.drawmodel(svg=1,all=True,browser=0,pdf=0,des=True,dot=True)
    ctx = dash.callback_context
    outvar=var[:]
    if ctx.triggered:
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger in ['var','down','up']:
            pass
            # print('kddddddddddddddkkddd')
        elif trigger == 'gv':
            pass
            xvar= select_var.split('(')[0]
            if xvar in mmodel.endogene or xvar in mmodel.exogene: 
                outvar = xvar
        value=mmodel.draw(outvar,dot=True,up=int(up),down=int(down))
        ctx_msg = json.dumps({
        'states': ctx.states,
        'triggered': ctx.triggered,
        'inputs': ctx.inputs
              }, indent=2)
        print(ctx_msg)
         
    
    return value,outvar


# @app.callback(Output("selected", "children"), [Input("gv", "selected")])
# def show_selected(value1):
#     value = value1
#     return html.Div(value)

# @app.callback(Output("selected-var", "children"), [Input('var', "value")])
# def show_var(value):
#     return html.Div(value)

if __name__ == "__main__":
    app.run_server(debug=False,port=5000)