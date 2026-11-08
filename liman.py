from ayarlar import OPERASYON_SURESI


# Gemiyi rıhtım kuyruğuna alır ve işini yalnızca yağmursuz saatlerde ilerletir.
def gemi(env, gemi_no, rihtim, yagmur_takvimi, kayitlar):
    kayit = {
        "gemi_no": gemi_no,
        "gelis_zamani": env.now,
        "yanasma_zamani": None,
        "ayrilis_zamani": None,
        "yagmur_beklemesi": 0,
    }
    kayitlar.append(kayit)

    # Rıhtımlar doluysa SimPy istekleri geliş sırasına göre kuyruğa koyar.
    with rihtim.request() as istek:
        # Yalnızca bu gemi rıhtım verilene kadar burada bekler.
        yield istek
        kayit["yanasma_zamani"] = env.now
        kalan_is = OPERASYON_SURESI

        while kalan_is > 0:
            # Bütün gemiler aynı saatin ortak hava durumunu okur.
            yagmurlu = yagmur_takvimi[int(env.now)]
            yield env.timeout(1)

            # Geçen saat yağmurluysa kalan iş değişmez; kuruysa bir saat azalır.
            if yagmurlu:
                kayit["yagmur_beklemesi"] += 1
            else:
                kalan_is -= 1

        kayit["ayrilis_zamani"] = env.now
        # with bloğundan çıkınca rıhtım bırakılır; yağmur molasında tutulur.
