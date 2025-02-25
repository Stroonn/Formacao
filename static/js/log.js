document.addEventListener("DOMContentLoaded", function() {
    const filtros = {
        data: "",
        produto: "",
        corretos: false,
        errados: false
    };

    function filtrarServicos() {
        // Se ambos os filtros corretos e errados estiverem marcados, mostrar tudo
        if (filtros.corretos && filtros.errados) {
            document.querySelectorAll(".info-process").forEach(el => {
                el.style.display = "flex";
            });
            return;
        }

        document.querySelectorAll(".info-process").forEach(el => {
            const data = el.getAttribute("data-data");
            const produto = el.getAttribute("data-produto");
            const erros = parseInt(el.getAttribute("data-erros"));

            let mostrar = true;

            console.log(filtros.data, data)

            if (filtros.data && filtros.data !== data) {
                mostrar = false;
            }
            if (filtros.produto && filtros.produto !== produto) {
                mostrar = false;
            }
            if (filtros.corretos && erros > 0) {
                mostrar = false;
            }
            if (filtros.errados && erros === 0) {
                mostrar = false;
            }

            el.style.display = mostrar ? "flex" : "none";
        });
    }

    // Filtro de Data
    document.querySelector("#filter-data-btn").addEventListener("click", function() {
        document.querySelector("#filter-data").style.display = "block";
    });

    document.querySelector("#filter-data").addEventListener("change", function() {
        const parsedDate = new Date(this.value);
        if (!isNaN(parsedDate)) {
            const day = String(parsedDate.getDate() + 1).padStart(2, '0');
            const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
            const year = parsedDate.getFullYear();
            filtros.data = `${day}/${month}/${year}`;
        } else {
            filtros.data = "";
        }
        document.querySelector("#filter-data-btn").textContent = filtros.data || "Todos";
        filtrarServicos();
    });

    document.querySelectorAll("#produto-dropdown .produto-option").forEach(option => {
        option.addEventListener("click", function() {
            filtros.produto = this.textContent === "Todos" ? "" : this.textContent;
            document.querySelector("#filter-produto-btn").textContent = this.textContent || "Todos";
            filtrarServicos();
        });
    });



    // Filtro de Produto is managed in the second DOMContentLoaded block to avoid duplicate event listeners.

    // Filtros de Corretos e Errados
    document.querySelector("#filter-corretos").addEventListener("change", function() {
        filtros.corretos = this.checked;
        filtrarServicos();
    });

    document.querySelector("#filter-errados").addEventListener("change", function() {
        filtros.errados = this.checked;
        filtrarServicos();
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const filterDataBtn = document.getElementById('filter-data-btn');
    const filterProdutoBtn = document.getElementById('filter-produto-btn');
    const dataDropdown = document.getElementById('data-dropdown');
    const produtoDropdown = document.getElementById('produto-dropdown');
  
    // Função para fechar dropdowns ao clicar fora
    document.addEventListener('click', function(event) {
      if (!event.target.closest('.select')) {
        dataDropdown.style.display = 'none';
        produtoDropdown.style.display = 'none';
      }
    });
  
    // Abrir/fechar dropdown de data
    filterDataBtn.addEventListener('click', function(event) {
      event.stopPropagation(); // Evita que o evento afete o fechamento do dropdown de produto
      // Alterna o estado do dropdown de data
      if (dataDropdown.style.display === 'block') {
        dataDropdown.style.display = 'none';
      } else {
        dataDropdown.style.display = 'block';
        produtoDropdown.style.display = 'none'; // Fecha o dropdown de produto ao abrir o de data
      }
    });
  
    // Abrir/fechar dropdown de produto
    filterProdutoBtn.addEventListener('click', function(event) {
      event.stopPropagation(); // Evita que o evento afete o fechamento do dropdown de data
      // Alterna o estado do dropdown de produto
      if (produtoDropdown.style.display === 'block') {
        produtoDropdown.style.display = 'none';
      } else {
        produtoDropdown.style.display = 'block';
        dataDropdown.style.display = 'none'; // Fecha o dropdown de data se abrir o de produto
      }
    });
  
    // Fechar dropdowns ao selecionar uma opção
    document.querySelectorAll('.produto-option').forEach(option => {
      option.addEventListener('click', function() {
        produtoDropdown.style.display = 'none';
      });
    });
  
    // Fechar dropdown de data ao selecionar uma data
    document.getElementById('filter-data').addEventListener('change', function() {
      dataDropdown.style.display = 'none';
    });
});
