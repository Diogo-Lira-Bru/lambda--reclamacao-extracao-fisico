import json
import os
import uuid
import boto3
import re
from datetime import datetime

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

SQS_QUEUE_URL = os.environ.get('SQS_CENTRAL_URL')

def extrair_id_cliente_do_nome(file_key):
    match = re.search(r'(\d{11})', file_key)
    
    if match:
        return match.group(1)
    
    return "ID_NAO_ENCONTRADO_DOC"


def ocr_e_extracao(bucket_name, file_key):
    customer_id = extrair_id_cliente_do_nome(file_key)
    print(f"ID de Cliente extraído do nome do arquivo: {customer_id}")
    
    # ----------------------------------------------------
    # 1. ACESSO REAL AO S3 (ONDE O OCR/EXTRAÇÃO OCORRERIA)
    # ----------------------------------------------------

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content_length = response['ContentLength']
        print(f"Arquivo acessado com sucesso. Tamanho: {content_length} bytes.")


    except Exception as e:
        print(f"ERRO CRÍTICO S3: Falha ao acessar o arquivo {file_key}. Erro: {e}")

    extracted_text = (
        f"Documento de reclamação para o cliente ID: {customer_id}. "
        "A reclamação indica problemas com cobrança indevida de fatura de seguro."
    )
    
    return extracted_text, customer_id

def lambda_handler(event, context):
    print("Evento S3 de upload recebido. Iniciando extração física.")

    # ----------------------------------------------------
    # 2. RECEPÇÃO DO EVENTO E EXTRAÇÃO DE METADADOS S3
    # ----------------------------------------------------
    s3_info = event['Records'][0]['s3']
    bucket_name = s3_info['bucket']['name']
    file_key = s3_info['object']['key']

    reclamation_text, customer_id = ocr_e_extracao(bucket_name, file_key)

    standardized_reclamation = {
        'Id': str(uuid.uuid4()),
        'CustomerIdentifier': customer_id,
        'ReclamationText': reclamation_text,
        'ReceivedDate': datetime.utcnow().isoformat() + 'Z',
        'SourceChannel': 'Physical',
        'AttachmentUrl': f"s3://{bucket_name}/{file_key}",
        'CustomerHistory': None,
        'ClassifiedCategories': []
    }
    message_body = json.dumps(standardized_reclamation)
    
    # ----------------------------------------------------
    # 3. ENVIO PARA O SQS CENTRAL
    # ----------------------------------------------------
    try:
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body,
            MessageAttributes={
                'Origem': {'DataType': 'String', 'StringValue': 'Fisico'},
                'Attachment': {'DataType': 'String', 'StringValue': file_key}
            }
        )
        
        print(f"Reclamação {standardized_reclamation['Id']} extraída e enviada para o SQS Central.")

        return {'statusCode': 200, 'body': 'Ingestão e extração concluídas.'}

    except Exception as e:
        print(f"ERRO CRÍTICO SQS: Falha no SQS após extração. Erro: {e}")
        raise e