import tkinter as tk
from tkinter.filedialog import asksaveasfilename
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime

caminho = ''
item = ''
n = ''

# função que separa o conteudo da coluna Parcelas (numero de parcelas e valor)
# e realiza a conta do valor total das parcelas

def extrai_valor_parcelas(df):

    # separa o valor de parcela utilizando expressão regular. extrai o valor com virgula que constam após o R$
    df['Valor Parcelas'] = df['Parcelas'].str.extract(r'R\$(\d+,\d+)')
    df['Valor Parcelas'] = df['Valor Parcelas'].fillna(0)
    df['Valor Parcelas'] = df['Valor Parcelas'].apply(lambda x: float(str(x).replace(',', '.')))

    # as parcelas aparecem ao lado da letra x como: '12x'
    # expressão que separa o numeros seguidos por 'x' 
    df['N Parcelas'] = df['Parcelas'].str.extract(r'(\d+)x')
    df['N Parcelas'] = df['N Parcelas'].fillna(0)
    df['N Parcelas'] = df['N Parcelas'].apply(lambda x: int(x))

    df[' Total parcelas'] = df['Valor Parcelas'] * df['N Parcelas']

    return df


def rodar_raspagem(item, n, caminho, search_url2):

    # incremento por pagina
    incremento = n - 1

    #montando a URL de pesquisa
    base_url = "https://lista.mercadolivre.com.br/"


    if ' ' in item:
        search_url = f"{base_url}{item.replace(' ', '-')}#D[A:{item.replace(' ', '%20')}]"

    else:
        search_url = f"{base_url}{item}#D[A:{item}]"

    # Realiza a requisição HTTP
    response = requests.get(search_url)

    # Verifica se a requisição foi bem-sucedida
    if response.status_code != 200:
        print(f"Erro ao acessar a URL: {search_url}")

    # Parsing do HTML 
    soup = BeautifulSoup(response.text, 'html.parser')

    # Classe html dos produtos normais
    # Encontra os elementos que contêm as informações do produto
    # todos os produtos tem essa classe, então usa-se o find all para trazer todos
    products = soup.find_all(class_='ui-search-result__content-wrapper')


    # Lista para armazenar os dados dos produtos patrocinados
    products_data_patr = []

    # Lista para armazenar os dados dos produtos normais
    products_data = []

    # Classe html dos produtos patrocinados
    # Encontra os elementos que contêm as informações do produto
    products_patr = soup.find(class_='ui-search-layout ui-search-layout--grid')

    df_patr = pd.DataFrame()

    if products_patr !=  None:
        
        products_patr = products_patr.find_all('li', class_='ui-search-layout__item')
        
        for i in range(len(products_patr)):

            
            # Obtém o nome do produto
            product_name = products_patr[i].find('h2', class_='ui-search-item__title').text.strip()
            
            # Obtém o preço do produto
            product_price = products_patr[i].find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript').text

            try:
            # avaliação
                product_eval = products_patr[i].find('span', class_='ui-search-reviews__rating-number').text
            except:
                pass

            try:
            # qtde avaliações
                product_qt_eval = products_patr[i].find('span', class_='ui-search-reviews__amount').text
            except:
                product_qt_eval = ''
            
            try: 
                # parcelas
                product_parc = products_patr[i].find('span', class_='ui-search-item__group__element ui-search-installments ui-search-color--BLACK')

                # Extrai o texto do elemento
                product_parc = product_parc.text
            except:
                pass

            # sem juros    
            try:
                product_juros = products_patr[i].find('div', class_='ui-search-price ui-search-price--size-x-tiny ui-search-color--LIGHT_GREEN')
                product_juros = product_juros.find(text='juros')

            except:
                pass
                # desconto
            try:
                product_discount = products_patr[i].find('span', class_='ui-search-price__discount').text.strip()
            except:
                product_discount = ''


            #link
            product_link = products_patr[i].find('a', class_='ui-search-item__group__element ui-search-link__title-card ui-search-link')

            # Extrai o atributo href que está o link do produto
            product_link = product_link['href']


            # DADOS LINK

            response2 = requests.get(product_link)

            # Verifica se a requisição foi bem-sucedida
            if response2.status_code != 200:
                print(f"Erro ao acessar a URL: {search_url}")

            # Parsing do HTML
            soup2 = BeautifulSoup(response2.text, 'html.parser')


            # Nome vendedor
            seller = ''  # Definindo um valor padrão
            try:
                info_element = soup2.find('span', class_='ui-pdp-color--BLUE ui-pdp-family--REGULAR')
                # Extrai o vendedor 
                seller = info_element.text
            except:
                pass

            # posição de venda na categoria, se possui
        
            try:
                position = soup2.find('div', class_ = 'ui-pdp-container__col col-1 ui-pdp-container--column-right mt-16 pr-16 ui-pdp--relative')
                if position.find('div', class_ = 'ui-pdp-container__row ui-pdp-container__row--highlights') != None:
                    
                    position = position.find_all('a', class_ = 'ui-pdp-promotions-pill-label__target')
                    position = position[1].text
                else:
                    position = ''
            except:
                position = ''                   
    
            # Frete
            try:
                product_fret = soup2.find('p', class_ = 'ui-pdp-color--GREEN ui-pdp-family--SEMIBOLD ui-pdp-media__title').text
                
            except:
                product_fret = ''

            try:
            # Novo/usado e qtde vendida
                
                situation = soup2.find('div',class_ = 'ui-pdp-header__subtitle')

                # Separa as informações 'Novo' e '+500 vendidos'
                info_parts = situation.text.split('|')

                # Remove os espaços em branco ao redor de cada parte
                info_parts = [part.strip() for part in info_parts]

                product_situation = info_parts[0]
                product_sells = info_parts[1]
            except:
                pass

                # Quant. de fotos e data foto
            try:
                
                # grade que estao as fotos
                images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')
                
                
                # quantidade de fotos
                images = len(images)
            except:
                pass
            
            # Data da Foto 
            url_list = []
            date_images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')    
            for img in date_images:
                date_images_url =  re.findall(r'https://\S+', str(img))
                url_list.append(date_images_url[0])


            # Categorias
            data_top = soup2.find_all('li',class_ = 'andes-breadcrumb__item')
            categories_list = []
            for cat in data_top:
                cat = cat.find('a', class_ = 'andes-breadcrumb__link')
                categories_list.append(cat['title'])
            patrocinado = 'sim'
    

            # Adicionando produtos em uma lista  
            products_data_patr.append({'Nome do Produto': product_name, 'Preço': product_price, 'Patrocinado': patrocinado, 
                                'Avaliação': product_eval, 'Qtde avaliações:': product_qt_eval,'Parcelas': product_parc, 
                                'Desconto': product_discount,'Frete': product_fret, 'Link': product_link, 'Vendedor': seller, 
                                'Posição': position, 'Situação': product_situation, 'Quant. vendida': product_sells, 
                                'Categorias': categories_list,'Quant. fotos': images, 'HTML Data':url_list })
            
            # Criando um Df dos produtos partocinados
            df_patr = pd.DataFrame(products_data_patr)

    # Produtos nao patrocinados

    for i in range(len(products)):

        
        # Obtém o nome do produto
        product_name = products[i].find('h2', class_='ui-search-item__title').text.strip()
        
        # Obtém o preço do produto
        product_price = products[i].find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript').text.strip()

        # se patrocinado caso, pagina seja com produtos na vertical
        product_patr = products[i].find('label', class_='ui-search-styled-label ui-search-item__pub-label')
            
        if product_patr == None:
            patrocinado = 'nao'

        else:
            patrocinado = 'sim'
        
        
        try:
        # avaliação
            product_eval = products[i].find('span', class_='ui-search-reviews__rating-number').text.strip()
        except:
            pass

        try:
        # qtde avaliações
            product_qt_eval = products[i].find('span', class_='ui-search-reviews__amount').text.strip()
        except:
            pass
        
        #frete gratis
        try:
            product_fret = products[i].find('span', class_='ui-pb-highlight').text.strip()
        except:
            product_fret = ''    

        try: 
            # parcelas
            product_parc = products[i].find('span', class_='ui-search-item__group__element ui-search-installments ui-search-color--BLACK')

            # Extrai o texto do elemento
            product_parc = product_parc.get_text(strip=True)
        except:
            pass

        # sem juros    
        try:
            product_juros = products[i].find('div', class_='ui-search-price ui-search-price--size-x-tiny ui-search-color--LIGHT_GREEN')
            product_juros = product_juros.find(text='juros')

        except:
            pass
            # desconto
        try:
            product_discount = products[i].find('span', class_='ui-search-price__discount').text.strip()
        except:
            product_discount = ''


        #link
        product_link = products[i].find('a', class_='ui-search-item__group__element ui-search-link__title-card ui-search-link')

        # Extrai o atributo href do elemento
        product_link = product_link['href']


        # DADOS LINK

        response2 = requests.get(product_link)

        # Verifica se a requisição foi bem-sucedida
        if response2.status_code != 200:
            print(f"Erro ao acessar a URL: {search_url}")

        # Parsing do HTML
        soup2 = BeautifulSoup(response2.text, 'html.parser')


        # Nome vendedor
        try:
            info_element = soup2.find('span',class_ = 'ui-pdp-color--BLUE ui-pdp-family--REGULAR')

            # Extrai o vendedor 
            seller = info_element.text
        except:
            pass
        
        
        # posição de venda na categoria, se possui
        
        try:
            position = soup2.find('div', class_ = 'ui-pdp-container__col col-1 ui-pdp-container--column-right mt-16 pr-16 ui-pdp--relative')
            if position.find('div', class_ = 'ui-pdp-container__row ui-pdp-container__row--highlights') != None:
                
                position = position.find_all('a', class_ = 'ui-pdp-promotions-pill-label__target')
                position = position[1].text
            else:
                position = ''
        except:
            position = ' '

        # Frete
        try:
            product_fret = soup2.find('p', class_ = 'ui-pdp-color--GREEN ui-pdp-family--SEMIBOLD ui-pdp-media__title').text
            
        except:
            product_fret = ''


        try:
        # Novo/usado e qtde vendida
            situation = soup2.find('div',class_ = 'ui-pdp-header__subtitle')
            # Separa as informações 'Novo' e '+500 vendidos'
            info_parts = situation.text.split('|')

            # Remove os espaços em branco ao redor de cada parte
            info_parts = [part.strip() for part in info_parts]
            product_situation = info_parts[0]
            product_sells = info_parts[1]
        except:
            pass

            # Quant. de fotos
        try:
            images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')
            images = len(images)
        except:
            pass

        #data da foto           
        url_list = []
        date_images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')    
        for img in date_images:
            date_images_url =  re.findall(r'https://\S+', str(img))
            url_list.append(date_images_url[0])
        
        
        # categorias
        data_top = soup2.find_all('li',class_ = 'andes-breadcrumb__item')

        categories_list = []
        

        for cat in data_top:

            cat = cat.find('a', class_ = 'andes-breadcrumb__link')
            categories_list.append(cat['title'])


        #criando a lista de produtos 

        products_data.append({'Nome do Produto': product_name, 'Preço': product_price, 'Patrocinado': patrocinado, 
                            'Avaliação': product_eval, 'Qtde avaliações:': product_qt_eval,'Parcelas': product_parc, 
                            'Desconto': product_discount,'Frete': product_fret, 'Link': product_link, 'Vendedor': seller, 
                            'Posição': position, 'Situação': product_situation, 'Quant. vendida': product_sells, 
                            'Categorias': categories_list,'Quant. fotos': images, 'HTML Data': url_list})

        # Cria um DataFrame com os dados dos produtos
        df = pd.DataFrame(products_data)

    # DataFrame vazio para armazenar todos os dados um para patrocinados e outro não patrocinado
    all_products_df = pd.DataFrame()
    all_products_df_patr = pd.DataFrame()

    for i in range(1, 5):
        

        # Realiza a requisição HTTP
        response = requests.get(search_url2)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code != 200:
            print(f"Erro ao acessar a URL: {search_url}")
            continue

        # Parsing do HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lista para armazenar os dados dos produtos desta iteração
        products_data = []

        # Encontra os elementos que contêm as informações do produto
        products = soup.find_all(class_='ui-search-result__content-wrapper')



        
        all_products_data_patr = []


        # produtos patrocinados
        
        products_patr = soup.find(class_='ui-search-layout ui-search-layout--grid')
        

        if products_patr !=  None:
            
            products_patr = products_patr.find_all('li', class_='ui-search-layout__item')

            for x in range(len(products_patr)):

                
                # Obtém o nome do produto
                product_name = products_patr[x].find('h2', class_='ui-search-item__title').text.strip()
                
                # Obtém o preço do produto
                product_price = products_patr[x].find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript').text.strip()

                try:
                # avaliação
                    product_eval = products_patr[x].find('span', class_='ui-search-reviews__rating-number').text.strip()
                except:
                    pass

                try:
                # qtde avaliações
                    product_qt_eval = products_patr[x].find('span', class_='ui-search-reviews__amount').text.strip()
                except:
                    pass
                
                #frete gratis
                try:
                    product_fret = products_patr[x].find('span', class_='ui-pb-highlight').text.striP()
                except:
                    product_fret = ''    

                try: 
                    # parcelas
                    product_parc = products_patr[x].find('span', class_='ui-search-item__group__element ui-search-installments ui-search-color--BLACK')

                    # Extrai o texto do elemento
                    product_parc = product_parc.get_text(strip=True)
                except:
                    pass

                # sem juros    
                try:
                    product_juros = products_patr[x].find('div', class_='ui-search-price ui-search-price--size-x-tiny ui-search-color--LIGHT_GREEN')
                    product_juros = product_juros.find(text='juros')

                except:
                    pass
                    # desconto
                try:
                    product_discount = products_patr[x].find('span', class_='ui-search-price__discount').text.strip()
                except:
                    product_discount = ''


                #link
                product_link = products_patr[x].find('a', class_='ui-search-item__group__element ui-search-link__title-card ui-search-link')

                # Extrai o atributo href do elemento
                product_link = product_link['href']


                # DADOS LINK

                response2 = requests.get(product_link)

                # Verifica se a requisição foi bem-sucedida
                if response2.status_code != 200:
                    print(f"Erro ao acessar a URL: {product_link}")

                # Parsing do HTML
                soup2 = BeautifulSoup(response2.text, 'html.parser')


                # Nome vendedor
                try:
                    #info_element = soup2.find('div', class_='ui-pdp-container__row ui-pdp--relative ui-pdp-with--separator--fluid pb-40')
                    #info_element = info_element.find('div',class_ = 'ui-pdp--sticky-wrapper ui-pdp--sticky-wrapper-right')
                    #info_element = info_element.find('div',class_ = 'ui-pdp-seller mb-20 mt-20 ui-pdp-seller__with-logo')
                    info_element = soup2.find('span',class_ = 'ui-pdp-color--BLUE ui-pdp-family--REGULAR')

                    # Extrai o vendedor 
                    seller = info_element.text

                except:
                    seller= ''

                # posição de venda na categoria, se possui
                
                try:
                    position = soup2.find('div', class_ = 'ui-pdp-container__col col-1 ui-pdp-container--column-right mt-16 pr-16 ui-pdp--relative')
                    if position.find('div', class_ = 'ui-pdp-container__row ui-pdp-container__row--highlights') != None:
                        
                        position = position.find_all('a', class_ = 'ui-pdp-promotions-pill-label__target')
                        position = position[1].text
                    else:
                        position = ''
                        
                except:
                    position = ''

                # Frete
                try:
                    product_fret = soup2.find('p', class_ = 'ui-pdp-color--GREEN ui-pdp-family--SEMIBOLD ui-pdp-media__title').text
                    
                except:
                    product_fret = ''


                try:
                # Novo/usado e qtde vendida
                    situation = soup2.find('div',class_ = 'ui-pdp-header__subtitle')

                    # Separa as informações 'Novo' e '+500 vendidos'
                    info_parts = situation.text.split('|')

                    # Remove os espaços em branco ao redor de cada parte
                    info_parts = [part.strip() for part in info_parts]

                    product_situation = info_parts[0]
                    product_sells = info_parts[1]
                except:
                    pass

                    # Quant. de fotos
                try:
    
                    images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')

                    images = len(images)
                except:
                    pass
            
                url_list = []
                date_images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')    
                for img in date_images:
                    date_images_url =  re.findall(r'https://\S+', str(img))
                url_list.append(date_images_url[0])

                # categorias
                data_top = soup2.find_all('li',class_ = 'andes-breadcrumb__item')

                categories_list = []
                

                for cat in data_top:

                    cat = cat.find('a', class_ = 'andes-breadcrumb__link')
                    categories_list.append(cat['title'])
            
                
            
                patrocinado = 'sim'
                
                # Adiciona os dados do produto à lista
                all_products_data_patr.append({'Nome do Produto': product_name, 'Preço': product_price, 'Patrocinado': patrocinado, 
                                'Avaliação': product_eval, 'Qtde avaliações:': product_qt_eval,'Parcelas': product_parc, 
                                'Desconto': product_discount,'Frete': product_fret, 'Link': product_link, 'Vendedor': seller, 
                                'Posição': position, 'Situação': product_situation, 'Quant. vendida': product_sells, 
                                'Categorias': categories_list,'Quant. fotos': images, 'HTML Data':url_list })

        # Cria um DataFrame com os dados dos produtos

            patr_temp_df = pd.DataFrame(all_products_data_patr)
            all_products_df_patr = pd.concat([all_products_df_patr, patr_temp_df], ignore_index=True)
            



    ##########################################################################################################################3






            for product in products:
                # Obtém o nome do produto
                product_name = product.find('h2', class_='ui-search-item__title').text.strip()

                #preço
                try:
                    product_price = product.find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript').text.strip()
                except:
                    product_price = product.find('span', class_='andes-money-amount__fraction').text.strip()


                # se patrocinado caso, pagina seja com produtos na vertical
                product_patr = products[i].find('label', class_='ui-search-styled-label ui-search-item__pub-label')
                

                
                

                if product_patr == None:
                    patrocinado = 'nao'
                    
                else:
                    patrocinado = 'sim'
                    


                try:
            # avaliação
                    product_eval = product.find('span', class_='ui-search-reviews__rating-number').text.strip()
                except:
                    pass

                try:
                # qtde avaliações
                    product_qt_eval = product.find('span', class_='ui-search-reviews__amount').text.strip()
                except:
                    pass
                
                #frete gratis
                try:
                    product_fret = product.find('span', class_='ui-pb-highlight').text.strip()
                except:
                    product_fret = ''    


                try: 
                # parcelas
                    product_parc = product.find('span', class_='ui-search-item__group__element ui-search-installments ui-search-color--BLACK')

                    # Extrai o texto do elemento
                    product_parc = product_parc.get_text(strip=True)
                except:
                    pass

                # sem juros    
                try:
                    product_juros = products.find('span', class_='ui-search-price ui-search-price--size-x-tiny ui-search-color--LIGHT_GREEN')
                    product_juros = product_juros.find(text='juros')

                except:
                    pass
                # desconto
                try:
                    product_discount = product.find('span', class_='ui-search-price__discount').text.strip()
                except:
                    product_discount = ''


                

                #link
                product_link = product.find('a', class_='ui-search-item__group__element ui-search-link__title-card ui-search-link')

                # Extrai o atributo href do elemento
                product_link = product_link['href']


                # DADOS LINK

                response2 = requests.get(product_link)

                # Verifica se a requisição foi bem-sucedida
                if response2.status_code != 200:
                    print(f"Erro ao acessar a URL: {search_url}")

                # Parsing do HTML
                soup2 = BeautifulSoup(response2.text, 'html.parser')

                # Vendedor
                try:
                    info_element = soup2.find('span',class_ = 'ui-pdp-color--BLUE ui-pdp-family--REGULAR').text

                    # Extrai o texto do elemento
                    seller = info_element
                except:
                    pass

                
                # posição de venda na categoria, se possui
            
                try:
                    position = soup2.find('div', class_ = 'ui-pdp-container__col col-1 ui-pdp-container--column-right mt-16 pr-16 ui-pdp--relative')
                    if position.find('div', class_ = 'ui-pdp-container__row ui-pdp-container__row--highlights') != None:
                        
                        position = position.find_all('a', class_ = 'ui-pdp-promotions-pill-label__target')
                        position = position[1].text

                    else:
                        position = ''
                        
                except:
                    position = ''

                # Frete
                try:
                    product_fret = soup2.find('p', class_ = 'ui-pdp-color--GREEN ui-pdp-family--SEMIBOLD ui-pdp-media__title').text
                    
                except:
                    product_fret = ''
                    

                    # Novo/usado e qtde vendida
                try:
                
                    #situation = soup2.find('div', class_='ui-pdp-container__col col-2 mr-32')
                    situation = soup2.find('div',class_ = 'ui-pdp-header__subtitle')


                    # Separa as informações 'Novo' e '+500 vendidos'
                    info_parts = situation.text.split('|')

                    # Remove os espaços em branco ao redor de cada parte
                    info_parts = [part.strip() for part in info_parts]

                    product_situation = info_parts[0]
                    product_sells = info_parts[1]
                except:
                    pass

                    # Quant. de fotos
                try:
                    images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')

                    images = len(images)
                except:
                    pass

                # data da foto
                    url_list = []
                    date_images = soup2.find_all('span',class_ = 'ui-pdp-gallery__wrapper')    
                    for img in date_images:

                        date_images_url =  re.findall(r'https://\S+', str(img))
                        url_list.append(date_images_url[0])


        #####################################

                # categorias
                data_top = soup2.find_all('li',class_ = 'andes-breadcrumb__item')

                categories_list = []
                

                for cat in data_top:

                    cat = cat.find('a', class_ = 'andes-breadcrumb__link')
                    categories_list.append(cat['title'])
            
        ###############################################

                # Adiciona os dados do produto à lista
                products_data.append({'Nome do Produto': product_name, 'Preço': product_price, 'Patrocinado': patrocinado, 
                                'Avaliação': product_eval, 'Qtde avaliações:': product_qt_eval,'Parcelas': product_parc, 
                                'Desconto': product_discount,'Frete': product_fret, 'Link': product_link, 'Vendedor': seller, 
                                'Posição': position, 'Situação': product_situation, 'Quant. vendida': product_sells, 
                                'Categorias': categories_list,'Quant. fotos': images, 'HTML Data': url_list})



        ####    # Incrementa a posição conforme a página seguinte
            
            n = n + incremento
            # Cria um DataFrame temporário com os dados dos produtos desta iteração
            temp_df = pd.DataFrame(products_data)

            # Concatena o DataFrame temporário ao DataFrame principal
            all_products_df = pd.concat([all_products_df, temp_df], ignore_index=True)




        # juntando os dataframes
        df_mercado_brinquedo = pd.concat([df, df_patr,all_products_df_patr,all_products_df], join = 'outer')
        df_mercado_brinquedo = extrai_valor_parcelas(df_mercado_brinquedo)
        df_mercado_brinquedo.drop(['Parcelas'], axis = 1, inplace = True)

        df_mercado_brinquedo['Categoria'] = item



        df_mercado_brinquedo['Categoria0'] = 0
        df_mercado_brinquedo['Categoria1'] = 0
        df_mercado_brinquedo['Categoria2'] = 0
        df_mercado_brinquedo['Categoria3'] = 0
        df_mercado_brinquedo['Categoria4'] = 0
        df_mercado_brinquedo['Categoria5'] = 0
        df_mercado_brinquedo['Categoria6'] = 0

        for i in range(len(df_mercado_brinquedo['Categorias'])):

            for x in range(len(df_mercado_brinquedo['Categorias'].iloc[i])):
                df_mercado_brinquedo[f'Categoria{x}'].iloc[i] = df_mercado_brinquedo['Categorias'].iloc[i][x]

                
                
        for i in range(len(df_mercado_brinquedo['Categorias'])):

                for x in range(1,7):
                    if df_mercado_brinquedo[f'Categoria{x}'].iloc[i] == 0:
                        df_mercado_brinquedo[f'Categoria{x}'].iloc[i] = df_mercado_brinquedo[f'Categoria{x-1}'].iloc[i]

    #copiando o dataset
    df= df_mercado_brinquedo.copy()

    df.shape

    #verificando o nome das colunas
    df.columns

    df2= df.copy()

    #verificando o tamanho do datafreme 
    df2.shape

    #escluindo linhas duplicadas
    df2 = df.drop_duplicates(subset=['HTML Data'])

    df3=df2.copy()

    df3.columns

    #separando link de anuncio e criando coluna anuncio 
    #separando numero do anuncio 
    padrao = r'/p\/([^#]+)'
    padrao2 =r'(MLB-\d*)'
    padrao3 = r'br\/(.*?)-'
    df3['anuncio'] = df3['Link'].str.extract(padrao, expand=False)
    df3['anuncio'].fillna(df3['Link'].str.extract(padrao2)[0], inplace=True)
    df3['anuncio'].fillna(df3['Link'].str.extract(padrao3)[0], inplace=True)

    df3['anuncio'].isna().sum()

    #VERIFICANDO O TAMANHO DO DATAFREME
    df3.shape

    def separar_conteudo(row):
        # Verifica se a coluna 'HTML Data' contém uma lista
        if isinstance(row['HTML Data'], list):
            # Converte a lista em uma string separada por vírgula
            html_data_str = ', '.join(row['HTML Data'])
        else:
            # Se já for uma string, mantém como está
            html_data_str = row['HTML Data']
        
        # Remove as tags HTML e divide o conteúdo em uma lista
        conteudos = html_data_str.strip('<p>').strip('</p>').split(', ')
        
        # Adiciona os conteúdos em novas colunas
        for i, conteudo in enumerate(conteudos):
            row[f'Conteudo_{i+1}'] = conteudo
        
        return row

    # Aplica a função a cada linha do DataFrame
    df3 = df3.apply(separar_conteudo, axis=1)

    # Verifica as colunas criadas
    colunas_originais = set(df3.columns)
    colunas_criadas_conteudo = set(df3.columns) - colunas_originais
    colunas_criadas_conteudo

    #separando e criando novas colunas com ML da foto e a data 
    #padrao_5 = r'-(.*?)_'
    padrao_6 =r'(?:.*?_){4}(.*?)-R'
    #string_exemplo = df4['Conteudo_1']  

    # Padrao regex para encontrar o que está entre '-' e '_'

    for coluna in colunas_criadas_conteudo:
        # Aplicar o padrão regex na coluna 'Conteudo_1'
        #df3[coluna + '_MLB1'] = df3[coluna].str.extract(padrao_5)
        df3[coluna +'_data_MLB1'] = df3[coluna].str.extract(padrao_6)
        #transformando a coluna em formato data 
        df3[coluna +'_data_MLB1'] = pd.to_datetime(df3[coluna +'_data_MLB1'])
        df3[coluna +'_data_MLB1'] = df3[coluna +'_data_MLB1'].dt.strftime('%d/%m/%Y')

    df3.head()


    # Transformando a coluna 'Avaliação' em números decimais
    df3['Avaliação'] = df3['Avaliação'].astype(float)

    # Arredondando os valores decimais para baixo e, em seguida, convertendo para números inteiros
    df3['Avaliação'] = df3['Avaliação'].apply(lambda x: int(x) if x.is_integer() else round(x))

    # Convertendo outras colunas para inteiros
    df3['N Parcelas'] = df3['N Parcelas'].astype(int) 
    df3['Quant. fotos'] = df3['Quant. fotos'].astype(int)

    # Removendo os parênteses da coluna 'Qtde avaliações:'
    df3['Qtde avaliações:'] = df3['Qtde avaliações:'].str.replace('(', '').str.replace(')', '')
    #transformando em numeros inteiros
    df3['Qtde avaliações:'].fillna(0, inplace=True)
    df3['Qtde avaliações:'] = df3['Qtde avaliações:'].astype(int)

    #transformando em numeros decimal 

    df3['Valor Parcelas'] = df3['Valor Parcelas'].astype(float)
    #df3[' Total parcelas'] = df3[' Total parcelas'].astype(float)

    #Transformando a coluna Quant. vendida
    df3['Quant. vendida'] = df3['Quant. vendida'].str.replace('mil', '000')
    df3['Quant. vendida'] = df3['Quant. vendida'].str.replace('+', '')
    df3['Quant. vendida'] = df3['Quant. vendida'].str.replace('vendido', '')
    df3['Quant. vendida'] = df3['Quant. vendida'].str.replace('s', '')
    df3['Quant. vendida'] = df3['Quant. vendida'].astype(int)

    #Função para converter uma string de preço em reais para float
    def converter_para_float(preco_string):
        # Remover caracteres não numéricos e converter para float
        preco_limpo = preco_string.replace("R$", "").replace(".", "").replace(",", ".")
        return float(preco_limpo)

    #Aplicar a função para toda a coluna 'Preço'
    df3['Preço'] = df3['Preço'].apply(converter_para_float)

    df3['Preço']

    def converter_para_float(preco):
        # Check if the value is already a float
        if isinstance(preco, float):
            return preco
        # Otherwise, clean and convert the string to float
        preco_limpo = str(preco).replace(".", "").replace(",", ".")
        return float(preco_limpo)

    # Apply the function to the entire 'Total parcelas' column
    df3[' Total parcelas'] = df3[' Total parcelas'].apply(converter_para_float)

    df3['taxas'] = 0
    df3.loc[df3['Preço'] < 79.0, 'taxas'] = 6

    df3['Data_atual'] = datetime.now().date()

    # Verifica se ambas as colunas 'Preço' e 'Quant. vendida' contêm valores numéricos
    if df3['Preço'].dtype in ['int', 'float'] and df3['Quant. vendida'].dtype == 'int':
        df3['total_de_vendas'] = df3['Preço'] * df3['Quant. vendida']
    else:
        # Converta as colunas para os tipos de dados apropriados antes de realizar a multiplicação
        df3['Preço'] = pd.to_numeric(df3['Preço'], errors='coerce')
        df3['Quant. vendida'] = pd.to_numeric(df3['Quant. vendida'], errors='coerce')
        df3['total_de_vendas'] = df3['Preço'] * df3['Quant. vendida']

    df3['total_de_vendas'].dtype

    df3.columns

    def selecionar_colunas_por_sufixo(dataframe, sufixo):
        colunas_selecionadas = [coluna for coluna in dataframe.columns if coluna.endswith(sufixo)]
        return dataframe[colunas_selecionadas]

    # Exemplo de uso:
    colunas_data = selecionar_colunas_por_sufixo(df3, '_MLB1')

    lista_colunas = colunas_data.columns.tolist()
    lista_colunas

    df3[lista_colunas] = df3[lista_colunas].apply(pd.to_datetime)

    df3['data_anuncio'] = df3[lista_colunas].min(axis=1)

    # Convertendo a coluna 'data_anuncio' para o tipo datetime, se não estiver
    df3['data_anuncio'] = pd.to_datetime(df3['data_anuncio'])

    # Substituir o dia 20 pelo dia 01
    df3['data_anuncio'] = df3['data_anuncio'].apply(lambda x: x.replace(day=1) if x.day == 20 else x)

    # Convertendo ambas as colunas para o formato datetime, se não estiverem
    df3['Data_atual'] = pd.to_datetime(df3['Data_atual'])
    df3['data_anuncio'] = pd.to_datetime(df3['data_anuncio'])

    # Calcula a diferença em dias entre a data atual e a data do anúncio para cada linha
    df3['quat_dias_do_anuncio'] = (df3['Data_atual'] - df3['data_anuncio']).dt.days
    df3['quat_dias_do_anuncio'].fillna(0, inplace=True)

    # Converter a coluna 'quat_dias_do_anuncio' para inteiro
    df3['quat_dias_do_anuncio'].fillna(0, inplace=True)

    # Converter a coluna 'quat_dias_do_anuncio' para inteiro
    df3['quat_dias_do_anuncio'] = df3['quat_dias_do_anuncio'].astype(int)

    df3.to_excel(caminho, index=False)



def salva_arquivo():
    global caminho
    file_path = asksaveasfilename(defaultextension=".xlsx")
    caminho = file_path

def chamar_raspagem():
    global item, n, caminho, search_url2
    item = itens_entry.get()
    n = int(n_entry.get())
    search_url2 = searchurl2_entry.get()
    rodar_raspagem(item, n, caminho, search_url2)

janela = tk.Tk()
janela.title("Raspagem de dados")
janela.geometry('570x550')

# Configurações de estilo
bg_color = "#f0f0f0"  # Cor de fundo
text_color = "#333"  # Cor do texto
font_family = "Arial"
font_size = 16

# Labels e entradas
intro_label = tk.Label(janela, text="Bem-vindo à interface de raspagem!", font=(font_family, 22), fg=text_color, bg=bg_color)
intro_label.pack(pady=10, fill="x")

tk.Label(janela, text="", bg=bg_color).pack(pady=10)  # Espaçamento

itens_label = tk.Label(janela, text="Insira o nome do item:", font=(font_family, font_size), fg=text_color, bg=bg_color)
itens_label.pack(pady=10, fill="x")
itens_entry = tk.Entry(janela, font=(font_family, font_size), fg=text_color, bg="white")
itens_entry.pack(pady=10)

searchurl2_label = tk.Label(janela, text="Insira o link da 2ª página do produto:", font=(font_family, font_size), fg=text_color, bg=bg_color)
searchurl2_label.pack(pady=10, fill="x")
searchurl2_entry = tk.Entry(janela, font=(font_family, font_size), fg=text_color, bg="white")
searchurl2_entry.pack(pady=10)

n_label = tk.Label(janela, text="Insira o número que aparece acima:", font=(font_family, font_size), fg=text_color, bg=bg_color)
n_label.pack(pady=10, fill="x")
n_entry = tk.Entry(janela, font=(font_family, font_size), fg=text_color, bg="white")
n_entry.pack(pady=10)

# Botões
salva_button = tk.Button(janela, text="Salvar arquivo", font=(font_family, font_size), command=salva_arquivo, fg=text_color, bg="gray")
salva_button.pack(pady=10)

roda_button = tk.Button(janela, text="Rodar raspagem", font=(font_family, font_size), command=chamar_raspagem, fg=text_color, bg="gray")
roda_button.pack(pady=10)

janela.mainloop()