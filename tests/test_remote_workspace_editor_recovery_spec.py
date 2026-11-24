from pathlib import Path


def test_recovery_contract_preserves_provenance_and_legacy_work():
    root = Path(__file__).parents[1] / 'docs/specs/remote_workspace_profile'
    text = (root / 'EDITOR_RECOVERY.md').read_text()
    for token in ('RRW-007I / INT-085', 'Git history is not authorship',
                  'Existing unreceipted legacy dirt stays untouched',
                  'Retain that failed candidate unchanged', 'Two renames are not an atomic',
                  'normal-path owner startup', 'readiness last', 'same-UID',
                  'duplicate JSON keys', 'cross-device', 'No new CLI options',
                  'the merged foundation revision recorded at cycle registration',
                  '## Visual Evidence', 'Text Equivalent'):
        assert token in text
    expansion = (root / 'OWNER_EXPANSION.md').read_text()
    assert 'EDITOR_RECOVERY.md' in expansion and 'Readiness remains success-only' in expansion
