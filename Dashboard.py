import pandas as pd
import streamlit as st 
import requests
import plotly.express as px 

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo}{valor:.2f} milhões'
        
st.title('DASHBOARD DE VENDAS')

url = 'https://labdados.com/produtos'
#criar filtros 
##Região e ano
regioes = ['Brasil','Centro-Oeste','Nordeste','Sudeste','Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = '' #não faz nada e mantem url padrão
    
todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True) #dizer que está marcado por default
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023) #valores min/max

#cria dicionário para verificar
query_string = {'regiao':regiao.lower(), 'ano': ano } #.lower para tratar 
    
#url_x = 'https://colab.research.google.com/drive/1mHIyXOBmIweSoIh2mwZqN8RHbdGBdt_9?usp=sharing'

response = requests.get(url, params= query_string) #parametro para inserir o filtro criado 
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

#criar o filtro vendedores
filtro_vendedor = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique()) #label, nomes para o multiselect
if filtro_vendedor:
    dados = dados[dados['Vendedor'].isin(filtro_vendedor)] # [[]].isin() altera ??

##Tabelas 
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending= False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

##Tabelas de quantidade de vendas 

##Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

##Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados, 
                                  lat = 'lat',
                                  lon ='lon',
                                  scope ='south america',
                                  size ='Preço',
                                  template ='seaborn',
                                  hover_name ='Local da compra',
                                  hover_data ={'lat': False, 'lon': False },
                                  title= 'Receita por estado')

fig_receita_mensal = px.line(receita_mensal, 
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash ='Ano',
                             title ='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto= True,
                             title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto= True,
                                title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title = 'Receita')

##Visulização no streamlit 
##abas
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])


#criando colunas 
with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        
with aba3:
    ##input para dar opção de tamanho do agregado
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5) ##em ordem -> nMin, nMáx, nDafault
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)') #joga o valor do input para dentro do head()
        st.plotly_chart(fig_receita_vendedores)
        
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)') #joga o valor do input para dentro do head()
        st.plotly_chart(fig_vendas_vendedores)
    
#st.dataframe(dados) foi comentado para não aprensentar o df no dash

#sempre que fechar 
#ativar -> 
#rodar -> streamlit run dashboard.py



