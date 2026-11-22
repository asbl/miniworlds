from __future__ import annotations


from app.security import (
    CODE_ALPHABET,
    decrypt_code,
    encrypt_code,
    gen_code,
    hash_code,
    make_student_token,
    verify_student_token,
)

SECRET = "unit-test-secret"


def test_gen_code_alphabet_and_length():
    code = gen_code(10)
    assert len(code) == 10
    assert all(c in CODE_ALPHABET for c in code)
    assert len({gen_code(12) for _ in range(100)}) == 100


def test_hash_code_stable_and_normalized():
    assert hash_code("abcd2345") == hash_code("  ABCD2345 ")


def test_code_encryption_roundtrip():
    enc = encrypt_code("ABCDEFGH23", SECRET)
    assert enc != "ABCDEFGH23"
    assert decrypt_code(enc, SECRET) == "ABCDEFGH23"


def test_student_token_roundtrip_and_tamper():
    tok = make_student_token(SECRET, 7, hash_code("ABCDEFGH23"), hours=1)
    payload = verify_student_token(SECRET, tok)
    assert payload["pid"] == 7
    assert verify_student_token(SECRET, tok + "x") is None
    assert verify_student_token("anderer-secret", tok) is None
    expired = make_student_token(SECRET, 7, hash_code("ABCDEFGH23"), hours=-1)
    assert verify_student_token(SECRET, expired) is None


def test_student_token_changes_with_code():
    t1 = make_student_token(SECRET, 7, hash_code("AAAAAAAAAA"), hours=1)
    t2 = make_student_token(SECRET, 7, hash_code("BBBBBBBBBB"), hours=1)
    assert verify_student_token(SECRET, t1)["ch"] != verify_student_token(SECRET, t2)["ch"]
