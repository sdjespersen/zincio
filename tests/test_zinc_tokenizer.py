from zincio import tokens
from zincio.zinc_tokenizer import tokenize
from zincio.tokens import NumberToken, TokenType, Token


def test_tokenize_datetime_with_tz():
    actual = list(tokenize("2020-05-17T23:47:08-07:00 Los_Angeles,"))
    expected = [
        Token(TokenType.DATETIME, "2020-05-17T23:47:08-07:00 Los_Angeles"),
        tokens.COMMA,
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_datetime_utc():
    actual = list(tokenize('mod:2020-03-23T23:36:40.343Z his'))
    expected = [
        Token(TokenType.ID, 'mod'),
        tokens.COLON,
        Token(TokenType.DATETIME, '2020-03-23T23:36:40.343Z'),
        Token(TokenType.ID, 'his'),
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_uri():
    actual = list(tokenize("`http://www.example.org`"))
    expected = [Token(TokenType.URI, "http://www.example.org"), tokens.EOF]
    assert actual == expected


def test_tokenize_ref_with_name():
    s = 'id:@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP"'
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'id'),
        tokens.COLON,
        Token(
            TokenType.REF,
            ('p:q01b001:r:0197767d-c51944e4 '
             '"Building One VAV1-01 Eff Heat SP"')),
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_ref_without_name():
    s = 'id:@p:q01b001:r:0197767d-c51944e4 nextTag'
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'id'),
        tokens.COLON,
        Token(TokenType.REF, 'p:q01b001:r:0197767d-c51944e4'),
        Token(TokenType.ID, 'nextTag'),
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_row_with_units():
    s = '2020-05-17T23:55:00-07:00 Los_Angeles,68.553°F'
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.DATETIME, '2020-05-17T23:55:00-07:00 Los_Angeles'),
        tokens.COMMA,
        NumberToken('68.553°F', 6),
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_long_string_valued_tag():
    s = ('actions:'
         '"ver:\\"3.0\\"\\ndis,expr\\n\\"Override\\",\\"pointOverride(\\$self,'
         ' \\$val, \\$duration)\\"\\n\\"Auto\\",\\"pointAuto(\\$self)\\"\\n"')
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'actions'),
        tokens.COLON,
        Token(
            TokenType.STRING,
            ('ver:\\"3.0\\"\\ndis,expr\\n\\"Override\\",\\"pointOverride(\\$'
             'self, \\$val, \\$duration)\\"\\n\\"Auto\\",\\"pointAuto(\\$self)'
             '\\"\\n')
        ),
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_multiple_lines():
    s = 'ts,val\n2020-05-17T23:47:08-07:00 Los_Angeles,\n\n'
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'ts'),
        tokens.COMMA,
        Token(TokenType.ID, 'val'),
        tokens.NEWLINE,
        Token(TokenType.DATETIME, '2020-05-17T23:47:08-07:00 Los_Angeles'),
        tokens.COMMA,
        tokens.NEWLINE,
        tokens.NEWLINE,
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_sentinels_in_values():
    s = ('ver:"3.0" hisEnd:M hisStart:M\n'
         'ts,v0 id:@vrt.x02.motion_state,v1 id:@vrt.x03.motion_amount\n'
         '2018-03-21T15:45:00+10:00 GMT-10,F,INF\n'
         '2018-03-21T15:50:00+10:00 GMT-10,N,NA\n'
         '2018-03-21T15:55:00+10:00 GMT-10,T,NaN\n\n')
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'ver'),
        tokens.COLON,
        Token(TokenType.STRING, '3.0'),
        Token(TokenType.ID, 'hisEnd'),
        tokens.COLON,
        Token(TokenType.RESERVED, 'M'),
        Token(TokenType.ID, 'hisStart'),
        tokens.COLON,
        Token(TokenType.RESERVED, 'M'),
        tokens.NEWLINE,
        Token(TokenType.ID, 'ts'),
        tokens.COMMA,
        Token(TokenType.ID, 'v0'),
        Token(TokenType.ID, 'id'),
        tokens.COLON,
        Token(TokenType.REF, 'vrt.x02.motion_state'),
        tokens.COMMA,
        Token(TokenType.ID, 'v1'),
        Token(TokenType.ID, 'id'),
        tokens.COLON,
        Token(TokenType.REF, 'vrt.x03.motion_amount'),
        tokens.NEWLINE,
        Token(TokenType.DATETIME, '2018-03-21T15:45:00+10:00 GMT-10'),
        tokens.COMMA,
        tokens.FALSE,
        tokens.COMMA,
        tokens.POS_INF,
        tokens.NEWLINE,
        Token(TokenType.DATETIME, '2018-03-21T15:50:00+10:00 GMT-10'),
        tokens.COMMA,
        tokens.NULL,
        tokens.COMMA,
        tokens.NA,
        tokens.NEWLINE,
        Token(TokenType.DATETIME, '2018-03-21T15:55:00+10:00 GMT-10'),
        tokens.COMMA,
        tokens.TRUE,
        tokens.COMMA,
        tokens.NAN,
        tokens.NEWLINE,
        tokens.NEWLINE,
        tokens.EOF,
    ]
    assert actual == expected


def test_tokenize_coords():
    s = ('ver:"3.0" hisStart:2020-05-18T03:00:00-07:00 Los_Angeles\n'
         'ts,v0 id:@somepoint\n'
         '2020-05-18T03:00:00-07:00 Los_Angeles,C(37.427539, -122.170244)\n\n')
    actual = list(tokenize(s))
    expected = [
        Token(TokenType.ID, 'ver'),
        tokens.COLON,
        Token(TokenType.STRING, '3.0'),
        Token(TokenType.ID, 'hisStart'),
        tokens.COLON,
        Token(TokenType.DATETIME, '2020-05-18T03:00:00-07:00 Los_Angeles'),
        tokens.NEWLINE,
        Token(TokenType.ID, 'ts'),
        tokens.COMMA,
        Token(TokenType.ID, 'v0'),
        Token(TokenType.ID, 'id'),
        tokens.COLON,
        Token(TokenType.REF, 'somepoint'),
        tokens.NEWLINE,
        Token(TokenType.DATETIME, '2020-05-18T03:00:00-07:00 Los_Angeles'),
        tokens.COMMA,
        Token(TokenType.COORD, 'C(37.427539,-122.170244)'),
        tokens.NEWLINE,
        tokens.NEWLINE,
        tokens.EOF,
    ]
    assert actual == expected
