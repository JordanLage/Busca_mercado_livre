from flask import Flask, render_template, request, jsonify, send_from_directory, session
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

app = Flask(__name__)

# Função para "pré carregar a página" antes de buscar os dados
def pre_load_site():
    url = "https://www.mercadolivre.com.br"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        requests.get(url, headers=headers, timeout=10)
        print("Acesso inicial ao site realizado com sucesso.")
    except requests.RequestException as e:
        print(f"Falha ao acessar o site: {e}")
    time.sleep(4)  

# Função para formatar o preço
def format_price(price):
    try:
        match = re.findall(r'\d+[\.,]?\d*', price)
        if not match:
            return "R$ 0,00"
        price_clean = ''.join(match).replace('.', '').replace(',', '.')
        price_float = float(price_clean)
        return f"R$ {price_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        return "R$ 0,00"

# Função para coletar detalhes do produto com tentativa dupla
def get_product_details(product_link):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for attempt in range(2):
        response = requests.get(product_link, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            try:
                seller_info = soup.find('div', class_='ui-pdp-seller__header__title')
                seller = seller_info.text.replace('Vendido por', '').strip() if seller_info else 'Não encontrado'
            except:
                seller = 'Não encontrado'

            loja_oficial = 'Sim' if 'Loja oficial' in seller else 'Não'
            seller = seller.replace('Loja oficial', '').strip()

            try:
                seller_link_tag = soup.find('div', class_='ui-seller-data-footer__container').find('a', class_='andes-button')
                seller_link = seller_link_tag['href'] if seller_link_tag else 'Não encontrado'
            except:
                seller_link = 'Não encontrado'

            try:
                frete = soup.find('p', class_='ui-pdp-color--GREEN ui-pdp-family--SEMIBOLD ui-pdp-media__title').text.strip()
            except:
                frete = 'Não especificado'

            try:
                svg_element = soup.find('svg', class_='ui-pdp-icon ui-pdp-icon--full ui-pdp-color--GREEN')
                tipo_envio = 'Full' if svg_element and svg_element.find('use', href='#full_icon') else 'Sem Full'
            except:
                tipo_envio = 'Não especificado'

            if tipo_envio == 'Full':
                frete = 'Frete grátis'

            try:
                situation = soup.find('div', class_='ui-pdp-header__subtitle')
                info_parts = situation.text.split('|')
                info_parts = [part.strip() for part in info_parts]
                product_situation = info_parts[0]
                product_sells = info_parts[1] if len(info_parts) > 1 else 'Não especificado'
            except:
                product_situation = 'Não especificado'
                product_sells = 'Não especificado'

            categories_list = []
            try:
                categories = soup.find_all('li', class_='andes-breadcrumb__item')
                for cat in categories:
                    link = cat.find('a', class_='andes-breadcrumb__link')
                    if link and 'title' in link.attrs:
                        categories_list.append(link['title'])
            except:
                categories_list = ['Não especificado']

            image_urls = []
            try:
                images = soup.find_all('span', class_='ui-pdp-gallery__wrapper')
                for img in images:
                    urls = re.findall(r'https://\S+', str(img))
                    image_urls.extend(urls)
            except:
                image_urls = []

            return seller, loja_oficial, frete, tipo_envio, product_situation, product_sells, categories_list, image_urls, seller_link
        
        else:
            print(f"Tentativa {attempt + 1} falhou para o link: {product_link}")
            time.sleep(2)  
    
    print(f"Erro ao acessar o link após 2 tentativas: {product_link}")
    return 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link', 'Acesse o link'

def scrape_mercado_livre(search_term):
    pre_load_site()

    pages = 2  # Definindo a quantidade de páginas fixa em 2
    base_url = f"https://lista.mercadolivre.com.br/{search_term.replace(' ', '-')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    all_products_data = []
    first_row = True

    for page in range(1, pages + 1):
        search_url = f"{base_url}_Desde_{(page - 1) * 50 + 1}"
        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Erro ao acessar a página de busca: {search_url}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Resultados encontrados
        try:
            results_quantity = soup.find('span', class_='ui-search-search-result__quantity-results').text.strip()
        except:
            results_quantity = 'Não especificado'

        # Buscas relacionadas
        related_searches = []
        try:
            related_list = soup.find('ul', class_='ui-search-top-keywords__list')
            if related_list:
                items = related_list.find_all('li', class_='ui-search-top-keywords__item')
                for item in items:
                    link = item.find('a', class_='ui-search-top-keywords__link')
                    if link and 'href' in link.attrs:
                        related_searches.append(link.text.strip())
        except:
            related_searches = ['Não especificado']

        # Buscando os produtos no novo layout
        products = soup.find_all('div', class_='ui-search-result__content-wrapper')

        if products:
            for product in products:
                try:
                    # Nome do produto
                    product_name = product.find('h2', class_='ui-search-item__title').text.strip() if product.find('h2', class_='ui-search-item__title') else 'N/A'

                    # Extraindo e formatando o preço do produto
                    price_span = product.find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript')
                    if price_span and price_span.has_attr('aria-label'):
                        raw_price = price_span['aria-label']
                        product_price = format_price(raw_price)
                    else:
                        product_price = "R$ 0,00"

                    # Verificando se o link do produto é válido
                    product_link_tag = product.find('a', class_='ui-search-link')
                    product_link = product_link_tag['href'] if product_link_tag else 'N/A'

                    seller, loja_oficial, frete, tipo_envio, product_situation, product_sells, categories_list, image_urls, seller_link = get_product_details(product_link)

                    # Avaliação do produto
                    try:
                        product_eval = product.find('span', class_='ui-search-reviews__rating-number').text.strip()
                    except AttributeError:
                        product_eval = 'Não encontrado'

                    # Desconto e outras informações
                    try:
                        product_discount = product.find('span', class_='ui-search-price__discount').text.strip()
                    except:
                        product_discount = ''

                    # Informações sobre parcelas
                    try:
                        product_parc = product.find('span', class_='ui-search-installments').get_text(strip=True)
                    except:
                        product_parc = ''

                    # Separando juros
                    if 'sem juros' in product_parc.lower():
                        juros_info = 'Sem juros'
                        product_parc = product_parc.replace('sem juros', '').strip()
                    else:
                        juros_info = 'Possui juros' if product_parc else 'Possui juros'
                        product_parc = product_parc.strip() if product_parc else ''

                    # Informação sobre cupons
                    try:
                        cupom_element = product.find('p', class_='ui-promotions-pill ui-pb-highlight-wrapper coupon')
                        if cupom_element:
                            cupom_text = cupom_element.find('span', class_='ui-pb-label').text.strip()
                            has_coupon = f"Sim ({cupom_text})"
                        else:
                            has_coupon = 'Não'
                    except:
                        has_coupon = 'Não'

                    sponsored_label = product.find('label', class_='ui-search-styled-label ui-search-item__pub-label')
                    sponsored = 'Sim' if sponsored_label and 'Patrocinado' in sponsored_label.text.strip() else 'Não'

                    all_products_data.append({
                        'Termo de busca': search_term if first_row else '',
                        'Quantidade de Resultados': results_quantity if first_row else '',
                        'Buscas Relacionadas': ', '.join(related_searches) if first_row else '',
                        'Nome do Produto': product_name,
                        'Preço': product_price,
                        'Parcelas': product_parc,
                        'Juros': juros_info,
                        'Desconto': product_discount,
                        'Cupom': has_coupon,
                        'Patrocinado': sponsored,
                        'Avaliação': product_eval,
                        'Frete': frete,
                        'Tipo de Envio': tipo_envio,
                        'Link': product_link,
                        'Vendedor': seller,
                        'Loja Oficial': loja_oficial,
                        'Link do Vendedor': seller_link,
                        'Situação': product_situation,
                        'Quantidade Vendida': product_sells,
                        'Categorias': ', '.join(categories_list),
                        'Imagens': ', '.join(image_urls),
                    })

                    first_row = False
                    time.sleep(1)  # Evitar sobrecarregar o servidor 
                except Exception as e:
                    print(f"Erro ao processar o produto: {e}")

    # Criar o DataFrame com todos os dados
    df = pd.DataFrame(all_products_data)

    save_path = f"{search_term.replace(' ', '_')}.xlsx"  
    df.to_excel(save_path, index=False) 

    return df, save_path 
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    search_term = request.form['search_term']
    df, save_path = scrape_mercado_livre(search_term) 

    if not df.empty:
        return jsonify({"status": "success", "file": save_path})
    else:
        return jsonify({"status": "error", "message": "Nenhum produto encontrado."})

    
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory('.', filename, as_attachment=True)

@app.route('/status')
def status():
    is_searching = session.get('is_searching', False)
    return jsonify({"is_searching": is_searching, "file": session.get('file', '')})

if __name__ == '__main__':
    app.run(debug=True)