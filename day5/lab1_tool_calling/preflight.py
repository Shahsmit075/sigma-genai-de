import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='amazon.nova-lite-v1:0',
    messages=[{
        'role': 'user',
        'content': [{'text': 'Reply with exactly three words: Bedrock is working'}]
    }]
)
print(response['output']['message']['content'][0]['text'])
# Expected: "Bedrock is working"
