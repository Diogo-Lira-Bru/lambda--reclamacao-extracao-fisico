import json
import os
import uuid
import boto3
import re
from datetime import datetime


s3_client = boto3.client('s3')
S3_BUCKET_NAME = 'reclamacoes'
S3_OUTPUT_PREFIX = 'lambda/extracao/fisico/processados/' 

def extrair_id_cliente_do_nome(file_key):
    match = re.search(r'(\d{11})', file_key)
    if match:
        return match.group(1)
    return "ID_NAO_ENCONTRADO_DOC"


def transformar_em_json_padrao(bucket_name, file_key):
    customer_id = extrair_id_cliente_do_nome(file_key)
    print(f"ID de Cliente extraído do nome do arquivo: {customer_id}")
    
    # ----------------------------------------------------
    # 1. ACESSO REAL AO S3 INPUT
    # ----------------------------------------------------
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content_length = response['ContentLength']
        print(f"Arquivo INPUT acessado com sucesso. Tamanho: {content_length} bytes.")

    except Exception as e:
        print(f"ERRO CRÍTICO S3 INPUT: Falha ao acessar o arquivo {file_key}. Erro: {e}")
        raise 

    # ----------------------------------------------------
    # 2. SIMULAÇÃO OCR E CRIAÇÃO DO OBJETO PADRONIZADO
    # ----------------------------------------------------
    reclamation_text = (
        f"Documento de reclamação para o cliente ID: {customer_id}. "
        "TRANSFORMADO PARA JSON PADRÃO."
    )
    
    standardized_reclamation = {
        'Id': str(uuid.uuid4()),
        'CustomerIdentifier': customer_id,
        'ReclamationText': reclamation_text,
        'ReceivedDate': datetime.utcnow().isoformat() + 'Z',
        'SourceChannel': 'Physical-ETL',
        'OriginalAttachmentUrl': f"s3://{bucket_name}/{file_key}",
        'CustomerHistory': None,
        'ClassifiedCategories': []
    }
    
    return standardized_reclamation


def lambda_handler(event, context):
    print("Evento S3 de upload recebido. Iniciando transformação de dados.")
    
    s3_info = event['Records'][0]['s3']
    input_bucket_name = s3_info['bucket']['name'] 
    file_key = s3_info['object']['key']
    
    if input_bucket_name != S3_BUCKET_NAME:
        print(f"ERRO: Bucket de origem não é o esperado ({S3_BUCKET_NAME}).")
        return {'statusCode': 400, 'body': 'Bucket de origem incorreto.'}


    standardized_reclamation = transformar_em_json_padrao(input_bucket_name, file_key)
    reclamation_id = standardized_reclamation['Id']

    message_body = json.dumps(standardized_reclamation)
    
    output_key = f"{S3_OUTPUT_PREFIX}{reclamation_id}.json"
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=output_key,
            Body=message_body,
            ContentType='application/json'
        )
        print(f"SUCESSO: JSON padronizado salvo em s3://{S3_BUCKET_NAME}/{output_key}")
        return {'statusCode': 200, 'body': f'Transformação de dados concluída. Arquivo final: {output_key}'}

    except Exception as e:
        print(f"ERRO CRÍTICO (PUT S3): Falha ao salvar o JSON transformado. Erro: {e}")
        raise e