Think very carefully about creating this pull request. I need you to:

1. **Determine the current task/branch context**:
   - Check if we're in a worktree directory (trees/*)
   - Identify the task name from the current branch or directory
   - Read the corresponding task file if $ARGUMENTS is not provided, otherwise use $ARGUMENTS as the task name

2. **Validate the implementation is complete**:
   - Verify all acceptance criteria in the task file are met
   - Check that all code follows the established patterns
   - Ensure proper error handling and type annotations are in place

3. **Run comprehensive quality checks**:
   - Execute: `uv run ruff check --fix --unsafe-fixes && uv run black . && uv run mypy . && uv run pytest`
   - Fix any issues that arise before proceeding
   - Verify all tests pass and code quality is maintained

4. **Perform manual testing**:
   - Run the validation commands specified in the task file
   - Test the new functionality with specific examples
   - Document what was tested and verified

5. **Prepare and create the commit**:
   - Ensure all changes are staged
   - Create commit with clear, concise message (NO Claude Code credit)
   - Follow the project's commit message standards

6. **Push and create PR**:
   - Push the branch: `git push -u origin feature/[task-name]`
   - Create PR with: `GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN gh pr create --title "[Title]" --body "[Body]"`

7. **PR content should include**:
   - **Summary**: Concise bullets of real functionality added
   - **Testing**: Specific commands run and what was verified
   - **Manual validation**: Steps taken to confirm functionality works

Task for PR: $ARGUMENTS

Focus on clear communication about what was delivered and how it was validated.