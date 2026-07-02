# Radigo File Organizer

このプロジェクトは、ラジオ録音ファイル（.aac形式）をGoogle Drive上で自動的に整理（振り分け）するためのPythonスクリプトです。ファイル名に含まれる日時と放送局コードを基に、内蔵された番組スケジュール表と照合し、設定ファイルに従って適切なフォルダへファイルを移動します。

## 主な機能

*   **ファイル整理**: Google Drive上の指定されたフォルダ内にある `.aac` ファイルを、放送局や番組ごとに分類されたフォルダへ移動します。
*   **番組スケジュールによる分類**: ファイル名の日時（曜日・開始時刻）と放送局コードから該当番組を判定し、番組別フォルダに振り分けます（対象外の放送局はスキップします）。
*   **設定ベースの動作**: `settings.yaml` ファイルを通じて、Google DriveのフォルダIDや基本的な保存パス、認証情報などを設定できます。
*   **Google Drive連携**: PyDrive2ライブラリを使用してGoogle Drive APIと連携し、ファイルのリスト取得、フォルダ作成、ファイル移動を行います。
*   **認証管理**: OAuth 2.0認証に対応し、認証エラーやアクセストークンのリフレッシュエラー発生時には再認証や再試行を行います。
*   **リトライ機能**: セッション失効やエラー発生時に、最大回数（デフォルト3回）まで再試行します。
*   **プログレスバー**: `tqdm` により処理中のファイル数の進行状況を表示します。
*   **ドライランモード**: `--dry-run` オプションを使用することで、実際にファイルを移動せずに処理の流れを確認できます。
*   **セッション更新**: `--refresh-session` オプションを使用して、Google Driveの認証セッションを強制的に更新できます。
*   **ログ出力**: 処理の進行状況やエラー情報をログファイル (`logs/` ディレクトリ内) に記録します。
*   **GitHub Actions連携**: `.github/workflows/move-radigo-files.yml` により、GitHub Actions上で手動実行が可能です。

## ファイル名形式

本スクリプトは [radigo](https://github.com/yyoshiki41/radigo) 等が生成する以下の形式のファイル名を前提とします。

```
YYYYMMDDHHMMSS-STATION_CODE.aac
```

*   `YYYYMMDDHHMMSS`: 録音開始日時（秒まで）。スクリプト内部では末尾2桁（秒）は無視して `%Y%m%d%H%M` で解析します。
*   `STATION_CODE`: 放送局コード（拡張子 `.aac` を除いた部分）。例: `TBS`, `LFR` など。

例: `20260102010000-TBS.aac`

## 分類ルール

ファイルは `settings.yaml` の `target_folder_path` を起点とし、以下のフォルダ構造に振り分けられます。

```
{target_folder_path}{STATION_CODE}/{番組フォルダ}/
```

例（`target_folder_path: audio/radio/` の場合）:
```
audio/radio/TBS/10-空気階段の踊り場/20260102010000-TBS.aac
```

番組フォルダは、スクリプト内の番組スケジュール表（`programs`）と録音日時の曜日・開始時刻が一致するエントリによって決定されます。対応する放送局コードは以下のとおりです（番組一覧は `radio_furiwake.py` 内の `programs` 定義を参照してください）。

| 放送局コード | 放送局 |
| --- | --- |
| TBS | TBSラジオ |
| LFR | ニッポン放送 |
| OBC | ラジオ大阪 |
| SBS | 静岡放送 |
| RN1 | 文化放送（RFID: RN1） |
| CRK | ラジオ関西 |
| STV | STVラジオ |

上記以外の放送局コードは「未知の放送局コード」としてログに記録され、移動対象外となります。

## 必要なもの

### ローカル実行時

*   Python 3.x
*   PyDrive2 (`pip install PyDrive2`)
*   tqdm (`pip install tqdm`)
*   Google Cloud Platform プロジェクト
    *   Google Drive API の有効化
    *   OAuth 2.0 クライアントIDとクライアントシークレット (通常 `client_secrets.json` としてダウンロード)

### GitHub Actions実行時

*   リポジトリのSecretsに以下の情報を設定する必要があります。
    *   `GOOGLE_CLIENT_ID`: Google Cloud PlatformのクライアントID
    *   `GOOGLE_CLIENT_SECRET`: Google Cloud Platformのクライアントシークレット
    *   `OUTPUT_FOLDER_ID`: Google Driveの処理対象ファイルが存在するフォルダID
    *   `TARGET_FOLDER_PATH`: Google Drive内の基本的な保存先パス (例: `audio/radio/`)
    *   `GOOGLE_CREDENTIALS_JSON`: Google Drive APIの認証情報 (通常 `credentials.json` の内容)

## セットアップ (ローカル実行時)

1.  **リポジトリのクローン**:
    ```bash
    git clone https://github.com/your_username/radigo_file-relocation.git
    cd radigo_file-relocation
    ```
2.  **依存関係のインストール**:
    ```bash
    pip install PyDrive2 tqdm
    ```
3.  **`client_secrets.json` の準備**:
    Google Cloud PlatformからダウンロードしたOAuth 2.0クライアントIDのJSONファイルをプロジェクトルートに配置するか、`settings.yaml` でパスを指定します。
4.  **`settings.yaml` の作成**:
    `settings.yaml.sample` をコピーして `settings.yaml` を作成し、環境に合わせて編集します。
    ```yaml
    client_config_backend: file # または 'settings' (GitHub Actionsでは 'settings' を使用)
    output_folder_id: <output_folder_id> # Google Driveの出力先フォルダID
    target_folder_path: audio/radio/ # Google Drive内の基本的な保存先パス (末尾に / を推奨)
    # client_config_backend: file の場合
    client_config_file: client_secrets.json # client_secrets.jsonへのパス
    # client_config_backend: settings の場合 (GitHub Actionsで使用)
    # client_config:
    #   client_id: "YOUR_CLIENT_ID"
    #   client_secret: "YOUR_CLIENT_SECRET"
    save_credentials: True
    save_credentials_backend: file
    save_credentials_file: credentials.json # 認証情報を保存するファイル名
    get_refresh_token: True
    oauth_scope:
      - https://www.googleapis.com/auth/drive
    ```
    初回実行時にはブラウザが起動し、Googleアカウントでの認証が求められます。認証後、`credentials.json` (または `save_credentials_file` で指定したファイル名) が作成され、次回以降の認証に使用されます。

## 実行方法

### ローカルでの実行

*   **通常実行**:
    ```bash
    python radio_furiwake.py
    ```
*   **ドライランモード**:
    ```bash
    python radio_furiwake.py --dry-run
    ```
*   **最大再試行回数の指定**:
    セッション失効やエラー発生時の再試行回数を指定します（デフォルト: 3）。
    ```bash
    python radio_furiwake.py --max-retries 5
    ```
*   **セッション更新**:
    Google Driveの認証情報を更新したい場合。
    ```bash
    python radio_furiwake.py --refresh-session
    ```
    このコマンド実行後、再度認証フローが開始され、新しい `credentials.json` が保存されます。

### GitHub Actionsでの実行

*   リポジトリの「Actions」タブから「Move_Radigo-Files」ワークフローを選択します。
*   「Run workflow」ボタンをクリックし、必要に応じて `dry_run` オプションを `true` または `false` に設定して実行します。
*   ワークフローは、設定されたSecretsを使用して `settings.yaml` と `credentials.json` を動的に生成し、スクリプトを実行します。
*   任意で `source_run_id`（上流の実行ID）を入力できます（省略可能）。
*   定期スケジュール実行は現在コメントアウトされており、手動実行 (`workflow_dispatch`) のみ利用可能です。

## 設定ファイル (`settings.yaml`)

*   `client_config_backend`: 認証クライアント設定の読み込み方法 (`file` または `settings`)。
*   `output_folder_id`: 処理対象のファイルが格納されているGoogle DriveのフォルダID。
*   `target_folder_path`: ファイルの移動先となるGoogle Drive内のベースパス。
*   `client_config_file`: `client_config_backend: file` の場合に、`client_secrets.json` ファイルへのパス。
*   `client_config`: `client_config_backend: settings` の場合に、クライアントIDとシークレットを直接記述。
*   `save_credentials`: 認証情報を保存するかどうか (True/False)。
*   `save_credentials_backend`: 認証情報の保存方法 (`file`)。
*   `save_credentials_file`: 保存する認証情報ファイルの名前 (例: `credentials.json`)。
*   `get_refresh_token`: リフレッシュトークンを取得するかどうか (True/False)。
*   `oauth_scope`: Google APIのアクセススコープ。

## ログ

スクリプトの実行ログは、プロジェクトルートの `logs` ディレクトリ内に、実行日時を含むファイル名で保存されます。
例: `logs/log_YYYYMMDDHHMMSS.txt`

同一時刻のファイル名が既に存在する場合は、`logs/log_YYYYMMDDHHMMSS-001.txt` のように通し番号（3桁）を付けて衝突を回避します。

## ライセンス

このプロジェクトは [LICENSE](./LICENSE) のもとで公開されています。
