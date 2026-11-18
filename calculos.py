"""SERS | GS 2026.2 - Horta comunitária com irrigação solar.
Cálculos de consumo e comparação de alternativas (mesma necessidade, 30 dias).
E (kWh) = P (W) x t (h) / 1000"""
import json

DIAS = 30
H0 = 2.0          # h/dia da bomba no cenário base (timer fixo)
REDUCAO = 0.30    # redução do tempo de bomba com sensor (ETEC Adamantina/SP: ~30% de água; premissa: tempo de bomba proporcional ao volume)
TARIFA = 0.95     # R$/kWh: Enel SP B1 com tributos ~0,866 (faturas 2026) x reajuste médio 10,18% de jul/2026
FATOR = 0.0385    # kg CO2e/kWh: média anual do SIN em 2023 (MCTI) = 38,5 kg/MWh
HSP, HSP_MIN, PR, WP = 4.2, 2.9, 0.75, 200  # kWh/m2.dia (Atlas Solar, média e junho), perf. ratio, painel (Wp)

def kwh(p, h, dias=DIAS):
    return p * h * dias / 1000

CTRL = kwh(3, 24)  # ESP32 + sensores + relé: 3 W, 24 h/dia
CEN = {
    "Base (bomba 370 W + timer)":      dict(p=370, solar=False, sens=False, custo=0),
    "A (rede + sensores)":             dict(p=370, solar=False, sens=True,  custo=350),
    "B (solar fotovoltaica + sensores)": dict(p=150, solar=True,  sens=True,  custo=1850),
}

base = kwh(370, H0)
res = {}
for nome, c in CEN.items():
    h = H0 * (1 - REDUCAO) if c["sens"] else H0
    tot = kwh(c["p"], h) + (CTRL if c["sens"] else 0)
    rede, sol = (0, tot) if c["solar"] else (tot, 0)
    eco = base - rede
    res[nome] = dict(
        consumo_kwh_mes=round(tot, 2), rede_kwh_mes=round(rede, 2),
        economia_kwh_mes=round(eco, 2), economia_pct=round(eco / base * 100, 1),
        economia_rs_mes=round(eco * TARIFA, 2),
        co2_evitado_kg_ano=round(eco * 12 * FATOR, 2),
        renovavel_pct=round(sol / tot * 100, 1),
        custo_implantacao_rs=c["custo"],
        payback_meses=round(c["custo"] / (eco * TARIFA), 1) if eco > 0 else None)

geracao = WP / 1000 * HSP * PR * DIAS
geracao_inv = WP / 1000 * HSP_MIN * PR * DIAS
print(f"Geração do painel de {WP} Wp: {geracao:.2f} kWh/mês (pior mês: {geracao_inv:.2f})")
for n, r in res.items():
    print(n, r)
json.dump(dict(cenarios=res, geracao_kwh_mes=round(geracao, 2), geracao_pior_mes_kwh=round(geracao_inv, 2)),
          open("dados.json", "w"), ensure_ascii=False, indent=2)
