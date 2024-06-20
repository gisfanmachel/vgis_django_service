
from dataclasses import dataclass, asdict
from toollib.guid import SnowFlake

@dataclass
class SnowflakeIDUtil:

    @staticmethod
    def snowflakeId():

        # worker_id  = 0,
        # datacenter_id = 0,
        snow = SnowFlake(worker_id_bits=0,datacenter_id_bits=0)

        return snow.gen_uid()
#278281003913445376
#17392738269396992
#8696383904808960
#17467422180114432
#17467316215480320
#278283890508955648
#283187993042944
#测试雪花ID
if __name__ == '__main__':
    for i in range(57):
        snow = SnowflakeIDUtil.snowflakeId()
        print(snow)
