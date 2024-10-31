# Busca mercado livre
Este projeto utiliza web scraping para buscar dados de produtos do Mercado Livre com base em termos de busca especificados. A aplicação é construída com Flask e permite que o usuário insira um termo de pesquisa, visualize e baixe os dados coletados em um arquivo Excel.

Funcionalidades
- Busca de dados de produtos do Mercado Livre com múltiplas tentativas para garantir a extração.
- Extração de informações detalhadas dos produtos, incluindo:
Nome do produto, preço e parcelas.
- Informações sobre o vendedor, situação do produto e quantidade vendida.
- Categorias, imagens, frete, avaliação, entre outros.
- Geração de um arquivo Excel com os dados coletados.
 Interface web para facilitar a entrada do termo de busca e download dos resultados.
Tecnologias Utilizadas
- Flask: Framework web para a construção da aplicação.
- BeautifulSoup: Biblioteca para busca de dados em HTML.
- Requests: Para realizar requisições HTTP.
- Pandas: Manipulação e armazenamento dos dados em DataFrames e exportação para Excel.

### Estrutura do Código
- app.py: Contém a lógica principal da aplicação, incluindo rotas, funções de busca e formatação de dados.
- templates/index.html: Página principal da interface web para entrada de dados e download do arquivo Excel.

### Considerações Importantes
- Limitações de busca: Raspagens muito frequentes ou de muitas páginas podem ser bloqueadas pelo site. Esse código implementa alguns time.sleep() para diminuir a carga das requisições.
- Acesso Inicial: O código faz uma tentativa inicial de acessar o Mercado Livre para evitar bloqueios ao longo da busca.
### Possíveis Melhorias
- Adição de Paginação Dinâmica: Tornar a quantidade de páginas configurável pelo usuário.
- Melhoria na Interface: Adicionar mais feedback sobre o andamento da busca para o usuário.
- Manipulação de Erros: Melhor tratamento de exceções para garantir que a aplicação lide bem com erros inesperados.
