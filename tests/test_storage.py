import sqlite3

from jobbot.models import Offer
from jobbot.storage import Store, fingerprint


def mk(source="adzuna", sid="1", title="Data Analyst H/F", company="ACME", city="lille"):
    return Offer(source, sid, title, company, "59 - Lille", "https://x", city_key=city)


def test_meme_offre_notifiee_une_seule_fois_par_profil():
    s = Store(":memory:")
    assert s.is_new("p1", mk())
    s.save("p1", mk(), notified=True)
    assert not s.is_new("p1", mk())
    assert s.is_new("p2", mk())  # un autre profil peut la recevoir


def test_meme_offre_sur_deux_sources_detectee():
    s = Store(":memory:")
    s.save("p1", mk(source="adzuna", sid="123", title="Data Analyst (H/F)"), notified=True)
    autre = mk(source="indeed", sid="abc", title="DATA ANALYST H/F", company="Acme")
    assert not s.is_new("p1", autre)


def test_offres_differentes():
    s = Store(":memory:")
    s.save("p1", mk(), notified=True)
    assert s.is_new("p1", mk(sid="2", title="Data Engineer"))
    assert s.is_new("p1", mk(sid="3", city="paris"))


def test_empreinte_ignore_hf_et_accents():
    a = mk(title="Ingénieur Data (H/F)", company="Société Générale")
    b = mk(title="ingenieur data F/H", company="SOCIETE GENERALE")
    assert fingerprint(a) == fingerprint(b)


def test_migration_base_v0_vers_profil_historique(tmp_path):
    db = tmp_path / "v0.db"
    c = sqlite3.connect(db)
    c.executescript("""
        CREATE TABLE offers (source TEXT NOT NULL, source_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
            title TEXT, company TEXT, city TEXT, url TEXT, first_seen TEXT DEFAULT (datetime('now')),
            notified INTEGER DEFAULT 0, PRIMARY KEY (source, source_id));
        CREATE INDEX idx_fp ON offers(fingerprint);
    """)
    o = mk()
    c.execute("INSERT INTO offers (source, source_id, fingerprint, title) VALUES (?,?,?,?)",
              (o.source, o.source_id, fingerprint(o), o.title))
    c.commit()
    c.close()
    s = Store(db)
    assert s.count() == 1
    assert not s.is_new("alternance-data", o)
    assert s.is_new("dev", o)
    Store(db)  # 2e ouverture : migration déjà faite, rien ne casse
    assert Store(db).count() == 1
