document.getElementById('search_button').addEventListener('click', function() {
    const searchTerm = document.getElementById('search_term').value;
    const loadingDiv = document.getElementById('loading');
    loadingDiv.classList.remove('hidden'); // Exibe a mensagem de loading

    fetch('/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'search_term=' + encodeURIComponent(searchTerm)
    })
    .then(response => response.json())
    .then(data => {
        loadingDiv.classList.add('hidden'); // Oculta a mensagem de loading
        const statusDiv = document.getElementById('status');
        statusDiv.innerHTML = ''; // Limpa o status anterior

        if (data.status === 'success') {
            statusDiv.textContent = "Pesquisa concluída! Planilha gerada: ";
            const downloadLink = document.createElement('a');
            downloadLink.href = '/download/' + encodeURIComponent(data.file);
            downloadLink.textContent = "Baixar " + data.file;
            downloadLink.download = data.file;
            statusDiv.appendChild(downloadLink); // Adiciona o link de download
        } else {
            statusDiv.textContent = "Erro: " + data.message;
        }
    });
});
