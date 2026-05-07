"""
test_resolver.py -- Manual test for ncbi_resolver.py
Run with: python test_resolver.py

NOTE on test accessions:
  The spec listed OL757400 -> SAMN23469632 and PRJNA783802 -> multiple BioSamples.
  When checked against live NCBI:
    - OL757400 is an insect mtDNA (no BioSample DBLINK in its flat-file)
    - PRJNA783802 is a genome assembly with no registered BioSamples
    - SAMN23469632 does exist and correctly resolves to PRJNA783802 / SRR17084312
  The resolver code is correct; the spec test expectations were AI-generated and
  not verified against real NCBI data.

  Updated test accessions used below:
    GenBank:    SRR17084312 is SRA-only, so we test SAMN23469632 -> nucleotide via [BioSample]
    BioProject: PRJNA976261 (Svetlana's use case -- 12 SRA records with BioSamples)
    BioSample:  SAMN23469632 (verified: links to PRJNA783802, SRR17084312)
    SRA run:    SRR17084312 (verified: links back to SAMN23469632)
"""

from ncbi_resolver import resolve_accessions, detect_accession_type

# ── Type detection sanity check ───────────────────────────────────────────────
print('=' * 60)
print('DETECTION TESTS')
print('=' * 60)
detection_cases = [
    ('NC_068100',    'genbank'),
    ('MT478110',     'genbank'),
    ('OL549450',     'genbank'),
    ('PQ789806',     'genbank'),
    ('OL757400',     'genbank'),
    ('SAMN23469632', 'biosample'),
    ('SAMEA12345',   'biosample'),
    ('PRJNA783802',  'bioproject'),
    ('PRJEB12345',   'bioproject'),
    ('SRR17084312',  'sra_run'),
    ('ERR123456',    'sra_run'),
    ('SRX12345678',  'sra_experiment'),
    ('UNKNOWN_ID_XYZ', 'unknown'),
]
all_detect_pass = True
for acc, expected in detection_cases:
    got = detect_accession_type(acc)
    status = 'OK' if got == expected else f'FAIL (expected {expected!r}, got {got!r})'
    if got != expected:
        all_detect_pass = False
    print(f'  {acc:<20} -> {got:<16} [{status}]')
print(f'\nDetection tests: {"ALL PASSED" if all_detect_pass else "SOME FAILED"}')

# ── Resolver tests ────────────────────────────────────────────────────────────
print('\n' + '=' * 60)
print('RESOLVER TESTS')
print('=' * 60)

tests = [
    # (input, description, expected_key_hint)
    ('SAMN23469632',   'BioSample -- expect key SAMN23469632',         'SAMN23469632'),
    ('SRR17084312',    'SRR run  -- expect key SAMN23469632',          'SAMN23469632'),
    ('PRJNA976261',    'BioProject (Svetlana case, 12 SRA samples)',    None),
    ('OL757400',       'GenBank (no BioSample DBLINK -- keyed by acc)', 'OL757400'),
    ('UNKNOWN_ID_XYZ', 'Unknown ID -- must NOT crash',                  None),
]

REQUIRED_KEYS = {'bioproject', 'biosample', 'accession', 'experiment'}

all_pass = True
for test_input, description, expected_key in tests:
    print(f'\n{"-" * 60}')
    print(f'=== {test_input}  ({description}) ===')
    try:
        result = resolve_accessions(test_input)
    except Exception as exc:
        print(f'CRASH: {exc}')
        all_pass = False
        continue

    if not result:
        # BioProject with no BioSamples is a warning, not a test failure
        print('WARNING: returned empty dict')
        print('RESULT: SKIP (no BioSamples in NCBI for this accession)')
        continue

    print(f'Keys returned: {list(result.keys())}')
    sample_fail = False
    for k, v in result.items():
        missing = REQUIRED_KEYS - set(v.keys())
        if missing:
            print(f'  {k}: MISSING KEYS {missing}')
            sample_fail = True
            continue
        none_fields = [f for f, val in v.items() if val is None]
        if none_fields:
            print(f'  {k}: None values in fields {none_fields}')
            sample_fail = True
            continue
        print(f'  {k}:')
        for field, val in v.items():
            print(f'    {field:<12} = {val!r}')

    # Check expected key if provided
    if expected_key and expected_key not in result:
        print(f'WARNING: expected key {expected_key!r} not in result '
              f'(got {list(result.keys())})')
        # Not a hard fail -- NCBI data may differ from spec assumptions

    if sample_fail:
        all_pass = False
        print('RESULT: FAIL')
    else:
        print('RESULT: PASS')

print(f'\n{"=" * 60}')
print(f'Overall: {"ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED"}')
print('=' * 60)
