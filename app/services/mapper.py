NAICS_TO_SIN = {
    "541511": "54151S",
    "541512": "54151S",
    "541611": "541611",
    "518210": "518210C",
}

class NaicsSinMapper:
    @staticmethod
    def get_recommended_sins(naics_codes):
        sins = set()
        for code in naics_codes:
            mapped = NAICS_TO_SIN.get(code.strip())
            if mapped:
                sins.add(mapped)
        return list(sins)
