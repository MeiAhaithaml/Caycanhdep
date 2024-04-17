from intasend import APIService
API_PUBLISHABLE_KEY ='ISPubKey_test_40e07e2d-32e8-429c-a515-7e09afa2773e'
API_TOKEN = 'ISSecretKey_test_acd2bae2-7794-4629-a163-d2805327f46f'

service = APIService(token=API_TOKEN,publishable_key=API_PUBLISHABLE_KEY,test=True)
create_order = service.collect.mpesa_stk_push(phone_number=2540332477829,email='nguyenhaibxlc74@gmail.com',amount=100,narrative='Purchase of items')

print(create_order)