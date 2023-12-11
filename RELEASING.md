
### Versioning

Version = MAJOR (>=1 year), MINOR (>= 1 month), PATCH

Version Status = Develop / Release


### Git

Branches
    develop: active development branch
    master: latest release
    vMAJOR.MINOR: release branch

Tags
    vMAJOR.MINOR.PATCH: tag for each release


### Release Process

 - Prepare the AliceVision release: https://github.com/alicevision/AliceVision
 - Update INSTALL.md and requirements.txt if needed
 - Source code
   - Create branch from develop: "rcMAJOR.MINOR"
   - Modify version in code, version status to RELEASE (meshroom/__init__.py)
   - Update the version of all the templates so their version corresponds to the release
   - Create Release note (using https://github.com/cbentejac/github-generate-release-note)
     - ```
	   ./github-generate-release-note.py -o alicevision -r Meshroom -m "Meshroom MAJOR.MINOR.PATCH" --highlights majorFeature feature --label-include bugfix ci,scope:doc,scope:build -s updated-asc
	   ```
   - PR to develop: "Release MAJOR.MINOR"
 - Build
   - Build docker & push to dockerhub
   - Build windows
 - Git
   - Merge "rcMAJOR.MINOR" into "develop"
   - Push "develop" into "master"
   - Create branch: vMAJOR.MINOR
   - Create tag: vMAJOR.MINOR.PATCH on Meshroom, qtAliceVision
   - Create branch from develop: "startMAJOR.MINOR"
 - Upload binaries on fosshub
 - Fill up Github release note
 - Prepare "develop" for new developments
   - Upgrade MINOR and reset version status to Develop
   - PR to develop: "Start Development MAJOR.MINOR"
 - Communication
   - Email on mailing-list: alicevision@googlegroups.com
   - Message on linkedin: https://www.linkedin.com/groups/13573776
   - Message on twitter: https://twitter.com/alicevision_org

### Upgrade a Release with a PATCH version

 - Source code
   - Create branch from rcMAJOR.MINOR: "rcMAJOR.MINOR.PATCH"
   - Cherry-pick specific commits or rebase required PR
   - Modify version in code
   - Update release note
 - Build step
 - Uploads
 - Github release note
 - Email on mailing-list

