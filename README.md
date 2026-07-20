# 📊 Validação de Apontamentos HT & Ocupação de Estufas (120x120)

Este é um aplicativo analítico desenvolvido em **Streamlit** para monitorar e auditar o processo de apontamento de percursos de tratamento térmico (**HT**). O objetivo principal é dar visibilidade operacional antecipada para evitar falhas de registros no sistema e mensurar o ganho de eficiência logística gerado pela transição para o modelo de cubagem otimizada por estrados.

O sistema consome os dados em tempo real diretamente de uma planilha do Google Sheets via API.

---

## 🛠️ Funcionalidades do Aplicativo

O sistema é dividido em duas frentes de trabalho dinâmicas:

### 1. 📋 Guia de Acompanhamento Detalhado (Aba Operacional)
Focada no dia a dia do time para rastreio rápido de erros e pendências:
*   **Priorização Lógica:** Lista automaticamente os percursos com status *Pendente* no topo, *Pronto* no meio e *Carregamento Concluído* na base.
*   **Filtro de Exceções:** Por padrão, a tabela exibe apenas o que precisa de ação imediata (Pendentes e Erros), limpando o que já está OK ou fluxos específicos da tela.
*   **Farol Visual na Coluna Status:**
    *   🔴 **Vermelho:** Alerta de Falha Crítica! Carregamento concluído no veículo, mas sem nenhum registro efetuado na coluna.
    *   🟠 **Laranja:** Status Pronto, porém aguardando auditoria/registro intermediário.
    *   🟡 **Amarelo:** Status Pendente/Aguardando (fluxo normal da rotina diária).
    *   🔵 **Azul:** Destinado ao Paraguai (isolado e monitorado via checkbox lateral).

### 2. 📊 Dashboard de Resultados & Raio-X de Transição (Aba Gerencial)
Focado em demonstrar o ROI do projeto de cubagem para a gerência:
*   **Auditoria de Aderência:** Compara o volume esperado (Previsto) contra o realizado (Apontado) e aponta em vermelho o *Gap de Lançamento (Pecado do Time)*.
*   **Volume Bruto:** Sumariza o total expedido de pallets (descontando o fluxo geográfico do Paraguai) e o volume físico acumulado de estrados processados.
*   **Raio-X de Transição Logística:** Desmuda os números para provar a eficiência:
    *   Demonstra o peso inevitável do **Estoques Passivos Anigos** (Base 12).
    *   Destaca a eficiência dos **Produtos Novos Otimizados** (Base 164), comprovando a redução drástica de ciclos de estufa e custos de energia.

---

## 📂 Estrutura do Projeto

```text
apontamento_120x120/
│
├── .gitignore          # Proteção contra arquivos temporários do Python
├── README.md           # Documentação do projeto (este arquivo)
├── requirements.txt    # Dependências do projeto (Streamlit e Pandas)
└── app.py              # Código-fonte principal da aplicação