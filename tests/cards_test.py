import aesops.cards

def test_corp_ids():
    corp_ids = aesops.cards.data.corp_ids()
    assert "Haas-Bioroid: Precision Design" in corp_ids
    assert "A Teia: IP Recovery" in corp_ids
    assert "LEO Construction: Labor Solutions" in corp_ids
    assert "Jinteki: Restoring Humanity" in corp_ids

def test_runner_ids():
    runner_ids = aesops.cards.data.runner_ids()
    assert "Az McCaffrey: Mechanical Prodigy" in runner_ids
    assert "Magdalene Keino-Chemutai: Cryptarchitect" in runner_ids
    assert "Captain Padma Isbister: Intrepid Explorer" in runner_ids

def test_get_faction():
    assert "weyland-consortium" == aesops.cards.data.get_faction("BANGUN: When Disaster Strikes")
    assert "nbn" == aesops.cards.data.get_faction("Nebula Talent Management: Making Stars")
    assert "jinteki" == aesops.cards.data.get_faction("AU Co.: The Gold Standard in Clones")
    assert "haas-bioroid" == aesops.cards.data.get_faction("LEO Construction: Labor Solutions")

    assert "criminal" == aesops.cards.data.get_faction("MuslihaT: Multifarious Marketeer")
    assert "anarch" == aesops.cards.data.get_faction('Ryo "Phoenix" Ono: Out of the Ashes')
    assert "shaper" == aesops.cards.data.get_faction("Dewi Subrotoputri: Pedagogical Dhalang")
