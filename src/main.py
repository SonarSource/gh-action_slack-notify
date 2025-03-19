import os


def main():
    github_env = os.environ.get('GITHUB_ENV')
    event_name = os.environ.get('GITHUB_EVENT')

    if event_name == "check_run":
        with open(github_env, 'a') as env:
            env.write("event_type=check_run\n")
    else:
        print("Retrieving failed check runs for check suite ID: XXX")


if __name__ == '__main__':
    main()
