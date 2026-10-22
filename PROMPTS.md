# PROMPTS.md

## Purpose

This document records how I used AI tools while developing TrustVault. I used AI as a coding assistant to understand implementation details, review existing code, troubleshoot errors, and improve security testing. I reviewed the suggested changes and used test results to check whether the implementation behaved as expected.

The project was developed incrementally. I focused on understanding the code, making targeted changes, and verifying important security requirements instead of blindly accepting generated code.

## 1. Reviewing document access control

**Prompt used:**

"I have implemented document access control in my Django project. Help me review whether the current logic correctly restricts users from accessing documents they don't own or haven't been granted permission to access. Explain any problems in my existing code and suggest only the changes that are necessary."

**My approach:**

I worked with the existing implementation and focused on the specific access-control logic instead of replacing entire files. I asked for explanations when I was unsure where a change belonged and reviewed how document ownership and granted permissions affected access.

**Verification:**

I ran the Django test suite and checked that a user without permission could not list, read, or download another user's document.

## 2. Testing permission levels

**Prompt used:**

"Review the permission rules in my Django document-sharing application. Help me verify the differences between read access and edit access. A user with read permission should be able to download a document but should not be allowed to edit its metadata, delete it, or share it with other users. Suggest minimal changes if the current implementation does not enforce these rules."

**My approach:**

I focused on the permissions required for each role and checked the behavior of the existing document endpoints. I used automated tests to verify that read-only and editor permissions did not provide more access than intended.

**Verification:**

I ran tests covering read access, editing restrictions, deletion restrictions, and permission-management restrictions.

## 3. Checking permission revocation

**Prompt used:**

"Help me review the permission-revocation flow in my existing Django application. After an owner revokes a user's access, that user must no longer be able to access or download the document. The audit trail should also record which user's permission was revoked and what access level was removed. Explain the required changes without rewriting the whole file."

**My approach:**

I examined the existing permission-revocation endpoint and its audit-event recording logic. I paid attention to recording the revoked permission level before deleting the permission record, so the audit event could preserve that information.

**Verification:**

I tested that a previously authorized user could no longer download the document after revocation and that the revocation details appeared in the audit trail.

## 4. Restricting administrator actions

**Prompt used:**

"Review my Django administrator endpoints and document deletion logic. Help me verify that only authorized administrators can access administrative activity and audit-verification endpoints, and that being an administrator does not automatically allow deleting another user's document unless that behavior is explicitly part of the policy."

**My approach:**

I checked the role checks on the administrative endpoints and the ownership requirements for document deletion. I used separate test cases to distinguish administrator access from document ownership.

**Verification:**

I tested that non-administrative users could not access administrative endpoints and that an administrator could not delete another user's document under the current ownership policy.

## 5. Improving audit-trail reliability

**Prompt used:**

"Help me review the audit-trail implementation in my Django project. I want audit events to record important document and permission actions, and I want to verify the event hash chain and detect changes to stored audit records. Explain what the current implementation can prove and what its limitations are."

**My approach:**

I reviewed the existing audit-event and hash-verification logic. I used the verification command and automated tests to understand how the chain behaved and to check whether modifying a stored event could be detected.

I also considered the distinction between detecting tampering and preventing it. A hash chain stored in the same database does not, by itself, guarantee that a sufficiently privileged attacker cannot rewrite the entire chain.

**Verification:**

I created an audit checkpoint, ran the audit-verification command, and tested both successful verification and tampering detection.

## 6. Validating document uploads

**Prompt used:**

"Review the document-upload validation in my Django application. Help me test whether unsupported file extensions are rejected and whether rejected uploads are prevented from creating document records. Point out additional file-validation risks that should be considered before deployment."

**My approach:**

I reviewed the existing upload serializer and endpoint and used a test case to check rejection of an unsupported extension. I also considered that checking a file extension alone is not sufficient to establish that a file is safe.

**Verification:**

I ran the upload-validation test and checked that an unsupported file type was rejected. Additional checks, such as file-size limits and content validation, should be confirmed before treating upload security as production-ready.

## 7. Diagnosing and fixing test failures

**Prompt used:**

"A Django security test is failing. Help me understand the traceback and identify the smallest code change needed to fix the underlying problem. Explain whether the change belongs in the test or in the application code, and do not assume the first proposed fix is correct."

**My approach:**

I used the traceback and test output to identify the failing behavior. I asked for clarification about exactly which lines needed to be changed and whether an existing code block should be replaced or only extended. After applying a change, I reran the tests to check the result.

**Verification:**

I reran the Django test suite after the relevant changes and used the test results to determine whether the failure had been resolved.

## 8. Reviewing security test coverage

**Prompt used:**

"Review my current Django security tests against the TrustVault requirements. Identify important access-control cases that are not covered yet, especially unauthorized document access, permission changes, revocation, audit visibility, and administrative endpoints. Recommend focused tests that fit the existing test structure."

**My approach:**

I added and ran focused tests for security requirements rather than relying only on successful requests from authorized users. I used the test results to check both allowed and denied operations.

**Verification:**

The test suite covers unauthorized document access, read-only restrictions, permission revocation, editor restrictions, upload validation, audit verification, administrative endpoint restrictions, permission-management restrictions, audit visibility, and administrator deletion restrictions.

At the time of writing, the suite contains 13 tests, and all 13 pass in the local Django test environment.

## 9. Using AI suggestions critically

I did not treat an AI-generated suggestion as proof that a feature was secure. When a suggestion was unclear, I asked for an explanation of the exact change. I then used the existing implementation, application behavior, and automated test results to evaluate the change.

Passing tests provide evidence for the scenarios covered by those tests. They do not prove that the application is free of security vulnerabilities.

## 10. Current limitations and next steps

The following items still require careful review before deployment:

- Confirm production settings, including `DEBUG`, `ALLOWED_HOSTS`, and secret-key handling.
- Confirm that authentication, session or token handling, and password policies are appropriate for the deployment.
- Verify that uploaded files cannot be accessed directly through a public media URL that bypasses document permissions.
- Review upload size limits, content validation, and handling of potentially malicious files.
- Check database and file-storage permissions and backup security.
- Consider storing audit checkpoints or signed audit evidence outside the database to make tampering harder to conceal.
- Run the security tests against the deployed application and review its actual configuration.

## Conclusion

AI assistance helped me review implementation choices, understand errors, and develop targeted security tests. I used explanations and test results to guide changes to the existing project. The test suite is an important verification step, but further deployment checks and security testing are needed before claiming that TrustVault is production-secure.