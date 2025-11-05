📄 lambda--reclamacao-extracao-fisico
  Função Lambda responsável por extrair, transformar e padronizar documentos físicos de reclamação recebidos via upload no Amazon S3, simulando OCR e gerando objetos JSON prontos para processamento posterior.

📌 Propósito
  Automatizar a ingestão de documentos físicos digitalizados, garantindo:
    Extração do identificador do cliente a partir do nome do arquivo
    Simulação de OCR para gerar texto da reclamação
    Padronização da estrutura de dados
    Armazenamento do resultado em formato JSON no S3

🔄 Fluxo de Execução
  Evento de upload no S3 dispara a função Lambda
  Validação do bucket de origem
  Extração do CPF/CNPJ do nome do arquivo
  Simulação de OCR e criação do objeto padronizado
  Persistência do JSON padronizado em um prefixo específico no S3

🧠 Lógica de Transformação
  A função transformar_em_json_padrao realiza:
    Extração do ID do cliente via regex (\d{11})
    Simulação de OCR com texto genérico
    Criação de objeto JSON com campos padronizados

Exemplo de saída:


{
  "Id": "c9a1e2f4-8b3d-4a2f-9c1e-abcdef123456",
  "CustomerIdentifier": "12345678901",
  "ReclamationText": "Documento de reclamação para o cliente ID: 12345678901. TRANSFORMADO PARA JSON PADRÃO.",
  "ReceivedDate": "2025-11-04T23:55:12.000Z",
  "SourceChannel": "Physical-ETL",
  "OriginalAttachmentUrl": "s3://reclamacoes/documentos/12345678901.pdf",
  "CustomerHistory": null,
  "ClassifiedCategories": []
}


🛡️ Tratamento de Erros
  Bucket incorreto: Retorno HTTP 400
  Falha no acesso ao S3: Log crítico e exceção
  Erro ao salvar JSON: Log crítico e exceção

📬 Armazenamento no S3
  O JSON padronizado é salvo em:
    Código
    s3://reclamacoes/lambda/extracao/fisico/processados/{UUID}.json

🧰 Tecnologias Utilizadas
  Componente	Tecnologia
  Função Serverless	AWS Lambda
  Armazenamento	Amazon S3
  Identificação	Regex + UUID
  Data e Hora	datetime (Python)
  Simulação OCR	Texto genérico
  
🧪 Testes Recomendados
  Arquivos com CPF/CNPJ válido no nome
  Arquivos sem identificador (fallback)
  Falhas simuladas de acesso ao S3
  Verificação do conteúdo e formato do JSON gerado

🔐 Segurança e Rastreabilidade
  Identificador único por reclamação
  URL original do documento preservada
  Logs detalhados de execução e falhas
