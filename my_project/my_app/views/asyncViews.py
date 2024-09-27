from django.http import JsonResponse
import asyncio

from rest_framework.decorators import action

my_random_num = 0


async def call_api():
    import random
    random_num = random.random()
    print("random_num:" + str(random_num))
    global my_random_num
    my_random_num = random_num
    # return {"num": random_num}


@action(detail=False, methods=['POST'])
async def my_view(request):
    # await asyncio.sleep(1)  # 模拟异步操作
    await call_api()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(call_api())
    obj = {'message': 'Hello, world!'}
    obj = {"num": my_random_num}

    return JsonResponse(obj)
