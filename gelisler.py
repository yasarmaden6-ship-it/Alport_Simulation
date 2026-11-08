import random

from ayarlar import GELIS_OLASILIGI, SIMULASYON_SURESI
from liman import gemi


# Her saatin başında en fazla bir gemi oluşturup liman sürecini başlatır.
def gemi_gelisleri(env, rihtim, yagmur_takvimi, kayitlar):
    gemi_no = 0
    for _ in range(SIMULASYON_SURESI):
        if random.random() < GELIS_OLASILIGI:
            gemi_no += 1
            # Her gemi aynı ortamda kendi bekleme ve çalışma sürecini yürütür.
            env.process(gemi(env, gemi_no, rihtim, yagmur_takvimi, kayitlar))

        # Yalnızca geliş süreci bir saat bekler; mevcut gemiler devam edebilir.
        yield env.timeout(1)
