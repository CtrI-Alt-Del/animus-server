# [1.22.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.21.3...v1.22.0) (2026-04-29)


### Features

* ANI-72 add ListUnfolderedAnalyses functionality with controller and use case ([f279408](https://github.com/CtrI-Alt-Del/animus-server/commit/f279408049928136500b241480cf8da9ea56f17a))

## [1.21.3](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.21.2...v1.21.3) (2026-04-28)


### Bug Fixes

* ANI-86 derive cloud run database url ([7929475](https://github.com/CtrI-Alt-Del/animus-server/commit/7929475c0cb21c012993ddc9d0adb8b586be77d4))

## [1.21.2](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.21.1...v1.21.2) (2026-04-28)


### Bug Fixes

* ANI-86 align server runtime configuration ([f4237d4](https://github.com/CtrI-Alt-Del/animus-server/commit/f4237d48d29f458efbaf006f8235517b2d8f2f39))
* ANI-86 allow container host binding ([2ee6957](https://github.com/CtrI-Alt-Del/animus-server/commit/2ee69575b5409c9db30ef9907363dcc2752602a0))
* ANI-86 satisfy env port typecheck ([00a8ba2](https://github.com/CtrI-Alt-Del/animus-server/commit/00a8ba2f16ba5f578e89e315c5617de4b12f7d7f))
* ANI-86 validate cloud run runtime before deploy ([aee2614](https://github.com/CtrI-Alt-Del/animus-server/commit/aee26140206cc4ca9e577ff7a60ff3b61fa22ff9))

## [1.21.1](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.21.0...v1.21.1) (2026-04-26)


### Bug Fixes

* ANI-63 update .gitignore to change opencode.jsonc to opencode.json ([3518546](https://github.com/CtrI-Alt-Del/animus-server/commit/351854618fbb559a3df112fbc7b54096e666e98e))

# [1.21.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.20.0...v1.21.0) (2026-04-22)


### Bug Fixes

* ANI-79 fix linter problems ([10341e0](https://github.com/CtrI-Alt-Del/animus-server/commit/10341e0f650c68c0c281f231609cd2c973fc5fd7))


### Features

* ANI-79 add endpoint to get analysis in processing ([eeca843](https://github.com/CtrI-Alt-Del/animus-server/commit/eeca843fda7aecfffd7c2af6ac40628c9acbd6c5))

# [1.20.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.19.0...v1.20.0) (2026-04-22)


### Features

* **library:** ANI-65 add library folders endpoints and persistence ([321b7b0](https://github.com/CtrI-Alt-Del/animus-server/commit/321b7b06c8ab75959dae3ce8504830ce96935d6c))
* **library:** ANI-65 enhance folder name validation and add additional tests for folder operations ([1f4d266](https://github.com/CtrI-Alt-Del/animus-server/commit/1f4d266c7d463eea37c59533083b087718aee08e))

# [1.19.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.18.0...v1.19.0) (2026-04-20)


### Bug Fixes

* ANI-83 include uv lock update in release automation ([1db7eb1](https://github.com/CtrI-Alt-Del/animus-server/commit/1db7eb1eaf9b93929d4826a7562007c88f82f096))
* ANI-83 support expanded precedent status values ([f94262d](https://github.com/CtrI-Alt-Del/animus-server/commit/f94262d8afeffcd1cd1b813d9f6b8b7d19c754bf))
* ANI-83 update CI workflow to use consistent quoting for Python version and environment variables ([da091e1](https://github.com/CtrI-Alt-Del/animus-server/commit/da091e10332184ecdec25c881ec6b4c4a488c087))


### Features

* ANI-83 add create-jira-ticket-prompt documentation for generating Jira tickets based on PRD or technical context ([9259ed6](https://github.com/CtrI-Alt-Del/animus-server/commit/9259ed6124d6b356c300818947f3ac5f135a9e67))
* ANI-83 rename precedent similarity fields and persist scoring metadata ([ab9bbe8](https://github.com/CtrI-Alt-Del/animus-server/commit/ab9bbe89fe0296ef718ccce30c814ce8537ea141))

# [1.18.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.17.0...v1.18.0) (2026-04-17)


### Bug Fixes

* ANI-77 manter filtros de precedentes nulos em analises legadas ([ed1b827](https://github.com/CtrI-Alt-Del/animus-server/commit/ed1b8276ac6fffca9461a21d6d39b441199d3e34))


### Features

* ANI-77 persist precedent search filters ([f203b17](https://github.com/CtrI-Alt-Del/animus-server/commit/f203b17027fe2fc8d552ccc03d792a3cf61149ea))

# [1.17.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.16.1...v1.17.0) (2026-04-15)


### Features

* ANI-84 add push notification provider interface ([c84cea7](https://github.com/CtrI-Alt-Del/animus-server/commit/c84cea76bd1cf3ab94dfe0d42c9eb06e02d38a37))

## [1.16.1](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.16.0...v1.16.1) (2026-04-15)


### Bug Fixes

* ANI-83 update FolderDto to include 'id' attribute initialization ([4d2ce1c](https://github.com/CtrI-Alt-Del/animus-server/commit/4d2ce1c948fc212d1db6b19aa7c7d540f590e400))

# [1.16.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.15.0...v1.16.0) (2026-04-15)


### Bug Fixes

* **auth:** ANI-70 format code for better readability ([f612be9](https://github.com/CtrI-Alt-Del/animus-server/commit/f612be9ff708895fe6458dd12049769d7bee7089))
* **auth:** ANI-70 honor reset password cooldown on forgot ([7e5c9f4](https://github.com/CtrI-Alt-Del/animus-server/commit/7e5c9f4150633b22a17b17befee5724ebe16868d))
* **migrations:** ANI-70 resolve analysis migration branch conflict ([e5073e1](https://github.com/CtrI-Alt-Del/animus-server/commit/e5073e15d257635703ccad7313e82d6fac14a4bc))


### Features

* **auth:** ANI-70 add reset password otp core flow ([1fb5cda](https://github.com/CtrI-Alt-Del/animus-server/commit/1fb5cda90ba13eabf5cd712ae267bab87b72b204))
* **auth:** ANI-70 expose otp reset password endpoints ([ca2f3f9](https://github.com/CtrI-Alt-Del/animus-server/commit/ca2f3f9ebfb1e4f0e7dd71b8b781f5ce4bf39a39))
* **notification:** ANI-70 send password reset emails with otp ([ac5ef5d](https://github.com/CtrI-Alt-Del/animus-server/commit/ac5ef5df654cd0bef725b4a37c4a89c0adb6af18))

# [1.15.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.14.0...v1.15.0) (2026-04-15)


### Bug Fixes

* ANI-99 format files and correct ruff target version ([5240935](https://github.com/CtrI-Alt-Del/animus-server/commit/524093580b9bf0cef75460fa23a7350a61c5de61))
* ANI-99 move supabase Mapping import to type checking ([f7be45a](https://github.com/CtrI-Alt-Del/animus-server/commit/f7be45a3906b7b9ec0948b279cdc2bb346f24712))


### Features

* ANI-99 migrate file storage provider to supabase ([3137ef5](https://github.com/CtrI-Alt-Del/animus-server/commit/3137ef568d76ec685c26c87f34e11dd5c0031a3c))

# [1.14.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.13.0...v1.14.0) (2026-04-05)


### Bug Fixes

* ANI-62 add cascade delete to intake foreign keys ([90395d2](https://github.com/CtrI-Alt-Del/animus-server/commit/90395d2c71e8e49425750d4630b2a65b290865c8))
* ANI-62 add env example fallback for CI settings loading ([da1c6a5](https://github.com/CtrI-Alt-Del/animus-server/commit/da1c6a5a0526120f87650537e0e13b81662870bf))
* ANI-62 add missing inngest event key to env example ([d8590fa](https://github.com/CtrI-Alt-Del/animus-server/commit/d8590fa9e3d05d7ee5e9868a0e5f4cd82fbcfd32))
* ANI-62 align analysis report precedent types ([ba14b42](https://github.com/CtrI-Alt-Del/animus-server/commit/ba14b42990e12d8d0ad7204239470c74f4beced2))
* ANI-62 align emulator env wiring for storage and qdrant ([da9acac](https://github.com/CtrI-Alt-Del/animus-server/commit/da9acacadc28ae93cb8444f7c3d6c1f955a5cdbe))
* ANI-62 narrow inngest readiness exception handling ([2f9a2c7](https://github.com/CtrI-Alt-Del/animus-server/commit/2f9a2c7fa506222f9269c2ccc71669dd24945217))
* ANI-62 resolve PR review issues across intake flows ([27e85e7](https://github.com/CtrI-Alt-Del/animus-server/commit/27e85e755fd62794f2841be15d15cdc0025095e3))
* ANI-62 stabilize inngest runtime readiness in integration tests ([14655e6](https://github.com/CtrI-Alt-Del/animus-server/commit/14655e652f77035aaa8c3a55f6e1a69dcb0c7ffa))


### Features

* ANI-50 add REST endpoint for PDF report generation ([ee9d39e](https://github.com/CtrI-Alt-Del/animus-server/commit/ee9d39e58f7aa09e8a0ecf38759a44be40a28c4f))
* ANI-50 implement core logic for PDF analysis report ([4389174](https://github.com/CtrI-Alt-Del/animus-server/commit/4389174069638e4044982b48b15be8398cf8dd1b))
* ANI-62 implement password reset and analysis report flows ([6d48b9c](https://github.com/CtrI-Alt-Del/animus-server/commit/6d48b9c9b90e8f15273f75fcdd0e1bc9244208f0))
* ANI-62 make petition summary request asynchronous ([ce2ebef](https://github.com/CtrI-Alt-Del/animus-server/commit/ce2ebef0acebc90a1b6e7978a5ff162447fba80b))

# [1.13.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.12.1...v1.13.0) (2026-04-05)


### Features

* **auth:** ANI-54 implement GET /auth/account endpoint ([d263ec6](https://github.com/CtrI-Alt-Del/animus-server/commit/d263ec6f4e76c421181271799c21bdfd72f3fe2a))

## [1.12.1](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.12.0...v1.12.1) (2026-04-05)


### Bug Fixes

* **auth:** ANI-36 add last fixes to reset flow ([5f7a34a](https://github.com/CtrI-Alt-Del/animus-server/commit/5f7a34ac0f90dbbc886da628474af73889d26bc8))
* **auth:** ANI-36 fix linter errors ([7004bf3](https://github.com/CtrI-Alt-Del/animus-server/commit/7004bf3498bac750bfd4dab3e4179fd61ed693fd))
* **auth:** ANI-36 fix linter problems ([bc65d67](https://github.com/CtrI-Alt-Del/animus-server/commit/bc65d6713f5011acdd01609d7a91d0c6ad3d91c3))

# [1.12.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.11.0...v1.12.0) (2026-04-03)


### Bug Fixes

* **auth:** ANI-38 register UpdateAccountController in auth router ([728e833](https://github.com/CtrI-Alt-Del/animus-server/commit/728e833ba1be0e03022a7dc339e759a97c30fe98))
* **auth:** ANI-38 Remove prd.md ([49080c6](https://github.com/CtrI-Alt-Del/animus-server/commit/49080c6a673e7b8d92cdf47c3020742f47e9f747))
* **auth:** ANI-38 restore GetAccountController and resolve router conflict ([fb01fe8](https://github.com/CtrI-Alt-Del/animus-server/commit/fb01fe88019493930a52d6d67c730d36a891dbec))


### Features

* **auth:** ANI-38 implement update account name endpoint ([de68428](https://github.com/CtrI-Alt-Del/animus-server/commit/de68428b64e40dc2446c8884ab4a022ed817f53e))

# [1.11.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.10.0...v1.11.0) (2026-04-02)


### Bug Fixes

* ANI-61 address PR review follow-ups ([3bd0e3d](https://github.com/CtrI-Alt-Del/animus-server/commit/3bd0e3df2e7c62c2efe79d3bf534112743f00dd0))
* ANI-61 align account endpoint path with auth controller contract ([fef1430](https://github.com/CtrI-Alt-Del/animus-server/commit/fef143029d630df9ad27c5c03c5295507d5b0ae4))


### Features

* ANI-61 add analysis report structure ([0c833f2](https://github.com/CtrI-Alt-Del/animus-server/commit/0c833f2fa0574f63cbbaa49a9bd82bf2458eea67))
* ANI-61 add intake analysis management endpoints ([7baa067](https://github.com/CtrI-Alt-Del/animus-server/commit/7baa06720d48f07fc0795107ae208c7d14be864f))
* ANI-61 add storage router with petition upload url endpoint ([c1f0100](https://github.com/CtrI-Alt-Del/animus-server/commit/c1f01006bf719b9a4e1020ec4f31c265c263409e))
* ANI-61 finalize petition replacement and summary flows ([aed3afe](https://github.com/CtrI-Alt-Del/animus-server/commit/aed3afec80e49ae5ae91138006ada610e920303a))
* ANI-61 implement petition replacement flow and intake read endpoints ([1e4a93a](https://github.com/CtrI-Alt-Del/animus-server/commit/1e4a93ab72d88003616f6ad4d5f4e519c4197925))

# [1.10.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.9.0...v1.10.0) (2026-04-01)


### Bug Fixes

* **auth:** ANI-29 restore legacy account profile route ([15690a6](https://github.com/CtrI-Alt-Del/animus-server/commit/15690a61d2685b6450fd5cfab71a303aacdb1988))


### Features

* **intake:** ANI-29 add analysis management endpoints ([d40c4db](https://github.com/CtrI-Alt-Del/animus-server/commit/d40c4dbdc5ec20383621a413674270018635766f))
* **intake:** ANI-29 add validation for limit parameter in analysis listing ([18ec896](https://github.com/CtrI-Alt-Del/animus-server/commit/18ec896c8005f0ce5c92823bd6eb339d7f2e3570))
* **intake:** ANI-29 implement analysis management endpoints and update pagination response handling ([7b49c5a](https://github.com/CtrI-Alt-Del/animus-server/commit/7b49c5ae25bc346269c593231d20f3f7ae27cd73))

# [1.9.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.8.0...v1.9.0) (2026-03-31)


### Bug Fixes

* ANI-53 handle missing account in GetAccountUseCase ([c9fc75c](https://github.com/CtrI-Alt-Del/animus-server/commit/c9fc75ce9b8fef22fce0b15cfcb3cb93fa60fe45))
* ANI-53 resolve copilot review issues on account endpoint ([7b4842f](https://github.com/CtrI-Alt-Del/animus-server/commit/7b4842f954cc40ffa14d2db26527c91fe0f463b0))
* **auth:** ANI-53 align repository contract and remove unused import ([d0ee6c1](https://github.com/CtrI-Alt-Del/animus-server/commit/d0ee6c1cfa4f09a48c7913e080c1af29bc537ed0))


### Features

* **auth:** ANI-53 add auth/me endpoint to retrieve user details ([3956b38](https://github.com/CtrI-Alt-Del/animus-server/commit/3956b38c8f450a8b9ae4ddb6ec1b499f5392d5bb))

# [1.8.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.7.0...v1.8.0) (2026-03-31)


### Features

* **intake:** ANI-44 add signed url endpoint ([66fb76f](https://github.com/CtrI-Alt-Del/animus-server/commit/66fb76f480352b5ba8729f21351cf05c0840f1be))

# [1.7.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.6.0...v1.7.0) (2026-03-31)


### Features

* ANI-48 add analysis petitions intake endpoint ([079d050](https://github.com/CtrI-Alt-Del/animus-server/commit/079d0507e61fea2c55335e4e8923225d467a2e90))
* ANI-48 implement intake precedents search and summary contracts ([758f3e7](https://github.com/CtrI-Alt-Del/animus-server/commit/758f3e7f44256e01ef31ae503d97ce9e7bb742f7))

# [1.6.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.5.0...v1.6.0) (2026-03-28)


### Bug Fixes

* ANI-45 resolve Ruff B023 and typing cast lint issues ([3556568](https://github.com/CtrI-Alt-Del/animus-server/commit/3556568de06fe45c95422bd013e71a398c05451e))


### Features

* ANI-45 add petition endpoints and summary flow ([6c48352](https://github.com/CtrI-Alt-Del/animus-server/commit/6c48352d55001d18b2d8e5366307f657a065bce8))
* ANI-45 implement precedent vectorization pipeline ([e9a15a5](https://github.com/CtrI-Alt-Del/animus-server/commit/e9a15a5daab249f566c780a199c380d3732e5e4b))

# [1.5.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.4.0...v1.5.0) (2026-03-28)


### Bug Fixes

* ANI-47 fix test speed ([f38073c](https://github.com/CtrI-Alt-Del/animus-server/commit/f38073c059f4cd06dfdd4e506f0efe49aa2bc219))
* ANI-47 fixed linter problems ([29cb106](https://github.com/CtrI-Alt-Del/animus-server/commit/29cb10685999c3cec68160494a761fb75e3999da))


### Features

* **intake:** ANI-47 add qdrant provider ([445aaef](https://github.com/CtrI-Alt-Del/animus-server/commit/445aaefeb83e65aaa4065bbb24713ffbaeafa35c))
* **intake:** ANI-47 add vectorize precedents job ([04a792a](https://github.com/CtrI-Alt-Del/animus-server/commit/04a792a1a710aaa9c1bfff907c7aeaea78421430))
* **intake:** ANI-47 finish vetorization job ([3a11469](https://github.com/CtrI-Alt-Del/animus-server/commit/3a11469681514d725d856d9d6aa76b9d919d2838))

# [1.4.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.3.0...v1.4.0) (2026-03-26)


### Bug Fixes

* ANI-57 address otp review feedback ([99d227f](https://github.com/CtrI-Alt-Del/animus-server/commit/99d227f7d58dcfc8aeb7b2af1c9d8281f799736b))
* ANI-57 enforce optional repository lookups and otp attempt limits ([8d0e30b](https://github.com/CtrI-Alt-Del/animus-server/commit/8d0e30b5727c6a255bad7e3b36fd65bb58b22fb9))
* ANI-57 reset verification attempts when generating otp ([d68c832](https://github.com/CtrI-Alt-Del/animus-server/commit/d68c8325383736733ee680472891da35c25f1e73))


### Features

* ANI-57 add auth seeding flow with faker support ([4a69c62](https://github.com/CtrI-Alt-Del/animus-server/commit/4a69c628918b1f4fb915017a64282c6129a8596a))
* ANI-57 add Dockerfile for multi-stage build with uvicorn setup ([756aafe](https://github.com/CtrI-Alt-Del/animus-server/commit/756aafe6f731d0c7340ac7a6d7ef4798da9168f6))
* ANI-57 implement otp email verification flow ([6cfa3c3](https://github.com/CtrI-Alt-Del/animus-server/commit/6cfa3c36656011353e181764d7d81776158370bc))

# [1.3.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.2.0...v1.3.0) (2026-03-25)


### Bug Fixes

* ANI-34 resolve PR review findings on naming and docs ([32f8d87](https://github.com/CtrI-Alt-Del/animus-server/commit/32f8d87f30a96923553a85dd19b0e9874e20c586))


### Features

* **auth:** ANI-34 add email/password sign-in endpoint and domain errors ([eb7035c](https://github.com/CtrI-Alt-Del/animus-server/commit/eb7035cccdf9edc0401a9798d2e0255c0e56a9bd))

# [1.2.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.1.0...v1.2.0) (2026-03-24)


### Features

* **auth:** #ANI-37 add sign in with google oauth ([aadbc4a](https://github.com/CtrI-Alt-Del/animus-server/commit/aadbc4a9906f44acc02310bb5ea75591e5210af6)), closes [#ANI-37](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-37)

# [1.1.0](https://github.com/CtrI-Alt-Del/animus-server/compare/v1.0.0...v1.1.0) (2026-03-23)


### Features

* **docs:** #ANI-56 add swagger docs ([f7cea7d](https://github.com/CtrI-Alt-Del/animus-server/commit/f7cea7d153f2086735a89c231f259bc4e00185ba)), closes [#ANI-56](https://github.com/CtrI-Alt-Del/animus-server/issues/ANI-56)

# 1.0.0 (2026-03-23)


### Bug Fixes

* ANI-21 resolve PR review feedback across core, docs, and tooling ([3d26712](https://github.com/CtrI-Alt-Del/animus-server/commit/3d26712095ff5325c6972d25ad0f52f555aad561))
* ANI-25 update PostgreSQL port mapping in docker-compose.yaml ([6027092](https://github.com/CtrI-Alt-Del/animus-server/commit/6027092345d2bcd2c03986e28bdc6e5cf786c5ec))


### Features

* ANI-21 bootstrap animus server structure and documentation ([b3c326e](https://github.com/CtrI-Alt-Del/animus-server/commit/b3c326e065e1099ff6aca65604096ef6be6342da))
* **auth:** ANI-35 implement sign-up workflow with persistence and email verification ([96b3516](https://github.com/CtrI-Alt-Del/animus-server/commit/96b35163f8f62fe623f65193f3937e9404677a0f))
* **auth:** ANI-52 add auth domain entities structures and interfaces ([60fbbab](https://github.com/CtrI-Alt-Del/animus-server/commit/60fbbab3a562bf96982025bd809b838ed700edcd))
* **intake:** ANI-52 add intake domain entities structures and interfaces ([a01b9f8](https://github.com/CtrI-Alt-Del/animus-server/commit/a01b9f813631aa137c5dac02b76e9d5e4aae5121))
* **storage:** ANI-52 add storage structures and provider interfaces ([473cf57](https://github.com/CtrI-Alt-Del/animus-server/commit/473cf57fab00bdaea205fc25b6364e74eff236a5))
