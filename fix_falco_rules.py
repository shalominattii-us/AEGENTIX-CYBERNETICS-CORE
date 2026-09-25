import re

path = 'C:/Aegentix/security/falco-aegentix-rules.yaml'
with open(path) as f:
    content = f.read()

orig_count = content.count('not in (')

# Fix 1: "X not in (LIST)" -> "not (X in (LIST))" for all field types
# Handles: container.image.repository, fd.sip, proc.name, fd.sport
# Also handles the case where "and MORE" follows (rule 49 fd.sport)

def replace_not_in(match):
    field = match.group(1)
    list_content = match.group(2)
    trailing = match.group(3) or ''  # " and ..." or empty
    return f'not ({field} in ({list_content})){trailing}'

content = re.sub(
    r'\b(container\.image\.repository|fd\.sip|proc\.name|fd\.sport) not in \(([^)]*)\)( and [^\n]*)?',
    replace_not_in,
    content
)

# Fix 2: Missing outer closing paren — "not (FIELD in (LIST)" at end of condition line
# These are lines where the patch added "not (" but didn't add the closing ")"
# Pattern: not (FIELD in (LIST)\n  →  not (FIELD in (LIST))\n
content = re.sub(
    r'not \((container\.image\.repository|fd\.sip|proc\.name) in \(([^)]*)\)\n',
    r'not (\1 in (\2))\n',
    content
)

# Fix 3: Rule 49 — fd.sport with "and fd.sport != 0" wrongly inside not()
# not (fd.sport in (7070, 7071, 7072, 7073) and fd.sport != 0) and fd.l4protocol...
# → not (fd.sport in (7070, 7071, 7072, 7073)) and fd.sport != 0 and fd.l4protocol...
old_49 = 'not (fd.sport in (7070, 7071, 7072, 7073) and fd.sport != 0) and fd.l4protocol in (tcp, udp)'
new_49 = 'not (fd.sport in (7070, 7071, 7072, 7073)) and fd.sport != 0 and fd.l4protocol in (tcp, udp)'
if old_49 in content:
    content = content.replace(old_49, new_49)
    print('Fixed rule 49: fd.sport != 0 moved outside not()')
else:
    print('WARNING: rule 49 pattern not found — may already be fixed or different')

# Fix 4: Rule 16 (SUID) — proc.exepath wrongly inside not()
# not (container.image.repository in (falcosecurity/falco) and proc.exepath exists...
# → not (container.image.repository in (falcosecurity/falco)) and proc.exepath exists...
old_16 = 'not (container.image.repository in (falcosecurity/falco) and proc.exepath exists and (proc.exepath suid or proc.exepath sgid)'
new_16 = 'not (container.image.repository in (falcosecurity/falco)) and proc.exepath exists and (proc.exepath suid or proc.exepath sgid)'
if old_16 in content:
    content = content.replace(old_16, new_16)
    print('Fixed rule 16 (SUID): proc.exepath moved outside not()')
else:
    print('WARNING: rule 16 pattern not found — checking alternatives...')
    # Try without the full trailing context
    alt_16 = 'not (container.image.repository in (falcosecurity/falco) and proc.exepath exists'
    if alt_16 in content:
        content = content.replace(
            'not (container.image.repository in (falcosecurity/falco) and proc.exepath exists',
            'not (container.image.repository in (falcosecurity/falco)) and proc.exepath exists'
        )
        print('Fixed rule 16 (SUID) with alternative match')

with open(path, 'w') as f:
    f.write(content)

# Verification
print(f'\n=== Verification ===')
print(f'Original "not in (" count: {orig_count}')
remaining_not_in = content.count('not in (')
print(f'Remaining "not in (" count: {remaining_not_in}')

if remaining_not_in > 0:
    print('REMAINING "not in" PATTERNS:')
    for i, line in enumerate(content.split('\n'), 1):
        if 'not in (' in line:
            print(f'  Line {i}: {line.strip()[:120]}')

# Check for missing outer parens
missing_parens = re.findall(r'not \((container\.image\.repository|fd\.sip|proc\.name) in \(([^)]*)\)\n', content)
if missing_parens:
    print(f'\nWARNING: {len(missing_parens)} "not (... in (...)" patterns still missing outer paren:')
    for m in missing_parens:
        print(f'  {m[0]} in ({m[1]})')

# Check rule 49
if 'not (fd.sport in (7070, 7071, 7072, 7073) and fd.sport != 0)' in content:
    print('ERROR: rule 49 still has fd.sport != 0 inside not()')
else:
    print('OK: rule 49 fixed')

# Check rule 16
if 'not (container.image.repository in (falcosecurity/falco) and proc.exepath' in content:
    print('ERROR: rule 16 still has proc.exepath inside not()')
else:
    print('OK: rule 16 fixed')

# Final check: any "not in" on container fields?
container_not_in = re.findall(r'container\.image\.repository not in', content)
if container_not_in:
    print(f'ERROR: {len(container_not_in)} "container.image.repository not in" still present')

fd_sip_not_in = re.findall(r'fd\.sip not in', content)
if fd_sip_not_in:
    print(f'ERROR: {len(fd_sip_not_in)} "fd.sip not in" still present')

print('\nDone.')
