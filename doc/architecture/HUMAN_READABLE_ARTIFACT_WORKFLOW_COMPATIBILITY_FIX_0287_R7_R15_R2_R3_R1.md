# Human-readable artifact workflow compatibility fix

The 0275 rule locks the three historical artifact-name strings into each
workflow. The readable-identity patch correctly stopped using those fixed names
for new uploads, but removed the strings entirely from the Projects workflow.

The fix restores them as explicit compatibility documentation beside the
identity step. They are not upload aliases and do not create duplicate
artifacts. The generated output names remain:

- `${{ steps.artifact-identity.outputs.request_name }}`;
- `${{ steps.artifact-identity.outputs.advisory_name }}`;
- `${{ steps.artifact-identity.outputs.manifest_name }}`.

Historical runs remain selected through the existing importer compatibility
contract.
