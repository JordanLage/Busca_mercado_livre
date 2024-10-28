# raspagem_mercadolivre

Código para raspagem de dados de produtos no mercado livre. 

O código faz a busca de um termo no mercado livre, encontra os produtos catalogados na página, e envia para uma planilha .xlsx as principais informações dos produtos. 

Utilizei flask de back-end para poder utilizar o script via web e permitir o download do arquivo gerado. 

Possui algumas melhorias a ser feita mas ja é um bom MVP.


Para utilizar o cófido precisa instalar as pendencias. Pode utilizar no terminal:

pip install -r requirements.txt

e depois 

python Busca_ml.py

Para executar o servidor local. 

Depois é só colocar o termo na caixa de pesquisa e aguardar a planilha gerada.
