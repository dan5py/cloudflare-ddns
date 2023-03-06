# Cloudflare DNS Record Updater

Update your DNS Record IP with this simple Python script.

Cloudflare API Reference: <https://developers.cloudflare.com/api/>

## Installation

Install the required modules

```bash
pip install -r requirements.txt
```

## Usage

```bash
python ddns-updater.py -r my.example.com
```

### Settings

In order to update the DNS record you need to provide:

- `email`, used to login to Cloudflare
- `token`, your API token
- `zone`, the target zone ID

You can either use the cli arguments or hardcode those information directly in the script under the `ARGUMENTS SECTION`.

### CLI Arguments

| Argument      | Default  | Description                                   | Required |
| :------------ | :------: | --------------------------------------------- | :------- |
| -e --email    |    /     | The account email used to login to Cloudflare | No       |
| -r --record   |    /     | The name of the record to update              | Yes      |
| -s --scoped   |  false   | Use scoped API token                          | No       |
| -t --token    |    /     | Your API token                                | No       |
| -z --zone     |    /     | The target zone ID                            | No       |
| -T --ttl      | 1 (auto) | TTL of the record                             | No       |
| -p --proxied  |  false   | Enable Cloudflare proxy                       | No       |
| -l --log-file |    /     | Path of the log file                          | No       |
| -v --verbose  |  false   | Enable verbose logging                        | No       |
| -h --help     |    /     | Show help message                             | No       |

## License

[MIT](https://choosealicense.com/licenses/mit/)
