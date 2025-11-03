import os
import argparse
import time
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime

def log_message(message):
    global log_file
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if 'log_file' not in globals():
        base_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
        counter = 1
        while os.path.exists(base_filename):
            base_filename = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}-{counter:03d}.txt")
            counter += 1
        log_file = base_filename

    with open(log_file, 'a', encoding='utf-8') as log_file_handle:
        log_file_handle.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def get_drive_session():
    """Google Driveのセッションを取得する関数"""
    gauth = GoogleAuth(settings_file='settings.yaml')
    try:
        # サービスアカウント認証
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)
        log_message("Google Driveセッションを取得しました (サービスアカウント)")
        return drive, gauth
    except Exception as e:
        log_message(f"サービスアカウントでのGoogle Driveセッション取得に失敗しました: {str(e)}")
        raise

def organize_files(dry_run=False, max_retries=3):
    retry_count = 0
    drive = None
    gauth = None

    while retry_count <= max_retries:
        try:
            if drive is None or gauth is None:
                # 初回またはセッション失効後の再取得
                drive, gauth = get_drive_session()

            # settings.yamlから出力フォルダのIDを取得
            if 'output_folder_id' not in gauth.settings:
                log_message("エラー: settings.yaml に output_folder_id が見つかりません。")
                raise ValueError("settings.yaml に output_folder_id が設定されていません。")
            output_folder_id = gauth.settings['output_folder_id']
            log_message(f"使用するoutput_folder_id: {output_folder_id}")

            if 'target_folder_path' not in gauth.settings:
                log_message("エラー: settings.yaml に target_folder_path が見つかりません。")
                raise ValueError("settings.yaml に target_folder_path が設定されていません。")
            config_target_folder_path = gauth.settings['target_folder_path'] # 変数名を変更
            log_message(f"使用するtarget_folder_path (設定値): {config_target_folder_path}")

            # ファイルを取得
            file_list = drive.ListFile({'q': f"'{output_folder_id}' in parents and trashed=false"}).GetList()

            # 番組情報をリストとして定義
            programs = {
                'TBS': [
                    {"folder": "10-空気階段の踊り場", "weekday": 1, "hour": 0},
                    {"folder": "11-JUNK 伊集院光の深夜の馬鹿力", "weekday": 1, "hour": 1},
                    {"folder": "20-アルコアンドピース DC GARAGE", "weekday": 2, "hour": 0},
                    {"folder": "21-佐倉綾音_論理×ロンリー", "weekday": 2, "hour": 22},
                    {"folder": "30-スタンド・バイ・見取り図", "weekday": 3, "hour": 0},
                    {"folder": "40-ハライチのターン", "weekday": 4, "hour": 0}
                ],
                'LFR': [
                    {"folder": "01-オードリーのオールナイトニッポン", "weekday": 6, "hour": 1},
                    {"folder": "12-キタニタツヤのANN0", "weekday": 1, "hour": 3},
                    {"folder": "21-星野源のオールナイトニッポン", "weekday": 2, "hour": 1},
                    {"folder": "51-ナインティナインのオールナイトニッポン", "weekday": 4, "hour": 1},
                    {"folder": "61-霜降り明星のオールナイトニッポン", "weekday": 5, "hour": 1}
                ],
                'OBC': [
                    {"folder": "40-サクラバシ919水曜", "weekday": 2, "hour": 23},
                    {"folder": "50-サクラバシ919木曜", "weekday": 3, "hour": 23}
                ],
                'SBS': [
                    {"folder": "週刊！しゃべレーザー", "weekday": 4, "hour": 23}
                ],
                'RN1': [
                    {"folder": "Anime & Seiyu Music Night", "weekday": 0, "hour": 20}
                ],
                'CRK': [
                    {"folder": "8年つづくラジオ", "weekday": 5, "hour": 0}
                ],
                'STV': [
                    {"folder": "12-キタニタツヤのANN0", "weekday": 1, "hour": 3},
                    {"folder": "22-あののANN0", "weekday": 2, "hour": 3},
                    {"folder": "42-佐久間宣行のオールナイトニッポン0", "weekday": 3, "hour": 3},
                    {"folder": "52-マヂカルラブリーのANN0", "weekday": 4, "hour": 3},
                    {"folder": "62-三四郎のオールナイトニッポン0", "weekday": 5, "hour": 3},
                    {"folder": "01-週替わりANN0", "weekday": 6, "hour": 3}
                ]
            }

            for file in file_list:
                file_name = file['title']
                if file_name.endswith('.aac'):
                    # ファイル名からメタデータを抽出
                    date_time, station_code = file_name.split('-')
                    station_code = station_code.split('.')[0]

                    # 日時オブジェクトを作成 (最後の "00" を無視)
                    file_date = datetime.strptime(date_time[:-2], "%Y%m%d%H%M")

                    # 適切なフォルダを決定
                    target_folder = f'{config_target_folder_path}{station_code}' # 設定ファイルから読み込んだ値を使用

                    if station_code in programs:
                        for program in programs[station_code]:
                            if file_date.hour == program["hour"] and file_date.weekday() == program["weekday"]:
                                target_folder += f'/{program["folder"]}'
                                break
                    else:
                        log_message(f"未知の放送局コード: {station_code}")
                        continue

                    if dry_run:
                        log_message(f"[ドライラン] ファイル {file_name} を {target_folder} に移動します。")
                    else:
                        try:
                            # フォルダを作成または取得
                            folder = create_or_get_folder(drive, target_folder)

                            # ファイルを移動
                            file['parents'] = [{'id': folder['id']}]
                            file.Upload()
                            log_message(f"ファイル {file_name} を {target_folder} に移動しました。")
                        except Exception as e:
                            log_message(f"ファイル {file_name} の処理中にエラーが発生しました: {str(e)}。リトライします。")
                            # セッションを再取得して再試行
                            drive, gauth = get_drive_session()
                            folder = create_or_get_folder(drive, target_folder)
                            file['parents'] = [{'id': folder['id']}]
                            file.Upload()
                            log_message(f"セッション再取得後、ファイル {file_name} を {target_folder} に移動しました。")

            log_message("ファイルの整理が完了しました。" if not dry_run else "ドライランが完了しました。")
            return  # 正常終了

        except Exception as e:
            retry_count += 1
            log_message(f"エラーが発生しました: {str(e)}。再試行 {retry_count}/{max_retries}")
            if retry_count <= max_retries:
                time.sleep(2)  # 少し待機してから再試行
            else:
                log_message(f"最大再試行回数に達しました。処理を中止します: {str(e)}")
                raise

def create_or_get_folder(drive, folder_path):
    try:
        folders = folder_path.split('/')
        parent_id = 'root'
        for folder_name in folders:
            query = f"title='{folder_name}' and '{parent_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
            folder_list = drive.ListFile({'q': query}).GetList()
            if folder_list:
                folder = folder_list[0]
            else:
                folder = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [{'id': parent_id}]})
                folder.Upload()
            parent_id = folder['id']
        return folder
    except Exception as e:
        log_message(f"フォルダの作成/取得中にエラーが発生しました: {str(e)}")
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ラジオ録音ファイルを整理するスクリプト')
    parser.add_argument('--dry-run', action='store_true', help='ドライランモードで実行（実際にファイルは移動しません）')
    parser.add_argument('--max-retries', type=int, default=3, help='セッション再取得の最大試行回数')
    args = parser.parse_args()
    organize_files(dry_run=args.dry_run, max_retries=args.max_retries)
