# lecture_summary_ice

강의 녹음 파일과 pdf자료를 이용해 공부에 도움을 주는 서비스입니다.


## Git 협업 전략

**Commit Convention**

| Commit Type | Description |
| --- | --- |
| Feat | 기능 개발 |
| Fix | 버그 수정 |
| Docs | 문서 수정 |
| Refactor | 코드 리팩토링 |
| Design | CSS 등 사용자 UI 변경 |
| Test | 로직 및 코드 테스트 |

**PR Convention**

| Icon | 사용법 | Description |
| --- | --- | --- |
| 🎨 Design | `:art` | UI/스타일 파일 추가/수정 |
| ✨ Feature | `:sparkles` | 새로운 기능 도입 |
| 🔥 Fix | `:fire` | 버그 수정 |
| ✅ Test | `:white_check_mark`   | 로직 및 코드 테스트 |
| ♻️ Refactoring | `:recycle` | 코드 리팩토링 |
| 📘 Docs | `:blue_book` | Feature 이외에 문서 생성 및 수정 |

**협업 전략**

**Git-flow 전략**

- Git-flow 전략을 기반으로 main, develop 브랜치와 feature 보조 브랜치를 운용.
- main, develop, Feat 브랜치로 나누어 개발을 하였습니다. - **main** 브랜치는 무결성 검증 이후 단계에서만 사용하는 브랜치입니다. - **develop** 브랜치는 개발 단계에서 git-flow의 master 역할을 하는 브랜치입니다. - **Feat** 브랜치는 기능 단위로 독립적인 개발 환경을 위하여 사용하고 merge 후 각 브랜치를 삭제해주었습니다.

**GitHub Role**

- 사용자는 먼저 Upstream Repository를 자신의 GitHub 계정으로 포크(fork)하고, 이 포크(fork)된 Origin Repository를 로컬 컴퓨터로 **Clone**하여 작업합니다.
- 그 후 개발한 변경 사항을 Origin Repository로 **Push**합니다. 이후 Upstream Repository로 풀 **PR**를 보내 변경 사항을 제안합니다.
- PR이 완료 된 후 Upstream Repository의 최신 변경 사항을 가져오기 위해 Local에서 풀(pull)을 사용합니다.

---

**개발을 시작할 때**

1. 개발을 시작할 때는 Upstream Repository에서 Issue를 생성합니다.
2. 이후 Issue에서 Origin Repository의 Dev Branch에서 새로운 Branch를 생성합니다
    - 이때 브랜치 이름은 다음을 따릅니다.
    - **새로운 기능 개발 : feature/#[Issue의 번호]**
    - **버그 픽스 : fix/#[Issue의 번호]**
    - **기능 리팩토링 : refactor/#[Issue의 번호]**
3. Loacl에서 Fetch를 통해 만든 New Branch(feature or fix or refactor)을 들고옵니다.
4. 해당 Branch로 checkout 이후 기능 개발을 진행합니다.

**개발을 종료할 때**

1. 기능 개발이 종료되면 Origin Repository의 Branch(feature or fix or refactor)로 변경 사항을 Push 합니다.
2. Origin Repository에서 Upstream Repository로 PR을 보냅니다.
3. Code Review 이후 마지막으로 Approve한 사람은 **Squash And Merge**를 합니다. `리뷰생략가능`
4. PR이 **Squash And Merge**되면 Local에서는 dev Branch로 checkout합니다.
5. Local에서 Upstream Repository의 dev Branch를 pull 받습니다.
6. 마지막으로 Origin Repository의 dev Branch를 Update하기 위해 Push를 해줍니다.

**Main Branch가 갱신될 때**

1. 만약 Release Version을 낼 때는 Upstream의 dev Branch에서 main Branch로 PR을 날립니다.
2. 해당 Repository의 모든 사용자가 Code를 재확인한 후 Merge를 합니다.
