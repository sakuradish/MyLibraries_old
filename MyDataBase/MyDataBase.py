# ===================================================================================
import sys
sys.path.append("../MyLogger/")
from MyLogger import MyLogger
MyLogger = MyLogger.GetInstance()
# ===================================================================================
import os
import datetime
import pandas as pd
import shutil
# ===================================================================================
## @brief Excelのデータを管理するクラス
class MyDataBase():
    ## @brief 初期化処理
    @MyLogger.deco
    def __init__(self, filename):
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.datapath = self.basedir + "/data/" + filename
        self.OnWriteCallback = []
        self.Initialize()
        self.Backup()
# ===================================================================================
    ## @brief インスタンス取得
    # @note
    # ファイルごとにインスタンスを生成する
    @classmethod
    @MyLogger.deco
    def GetInstance(cls, filename):
        if not hasattr(cls, 'this_'):
            cls.this_ = {}
        if not filename in cls.this_:
            cls.this_[filename] = cls(filename=filename)
        return cls.this_[filename]
# ===================================================================================
    ## @brief データベース初期化処理
    # @note
    @MyLogger.deco
    def Initialize(self):
        # ファイル/フォルダがなければ作成
        if not os.path.exists(os.path.dirname(self.datapath)):
            os.makedirs(os.path.dirname(self.datapath))
        if not os.path.exists(self.datapath):
            pd.DataFrame(columns=['timestamp/date', 'timestamp/time']).to_excel(self.datapath, index=False)
            # pd.DataFrame().to_excel(self.datapath, index=False)
            MyLogger.info(self.datapath, ' is initialized')
        # DataFrame読み込み
        self.DFRead()
        # Timestamp用の列がなければ追加してファイル更新
        if not 'timestamp/date' in self.df and not 'timestamp/time' in self.df:
            dt = datetime.datetime.now()
            self.df.insert(0, 'timestamp/date', dt.strftime("%Y/%m/%d"))
            self.df.insert(1, 'timestamp/time', dt.strftime('%X'))
            self.DFWrite()
# ===================================================================================
    # @brief バックアップ処理
    @MyLogger.deco
    def Backup(self):
        folder = self.basedir + "/backup/" + str(datetime.date.today()) + "/"
        file = folder + os.path.basename(self.datapath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if not os.path.exists(file):
            shutil.copy2(self.datapath, file)
# ===================================================================================
    ## @brief データフレームをxlsxから読み込み
    @MyLogger.deco
    def DFRead(self):
        self.df = pd.read_excel(self.datapath, engine='openpyxl')
        self.columns = list(self.df.columns)[2:]
        self.rows = list(self.df.index)
# ===================================================================================
    ## @brief データフレームをxlsxに書き込み
    # @note
    @MyLogger.deco
    def DFWrite(self):
        self.df.to_excel(self.datapath, index=False)
        self.OnWrite()
# ===================================================================================
    ## @brief データフレームから指定列の重複を削除
    # @note
    # keepに'first/last'を設定することで残す行を選択可能
    @MyLogger.deco
    def DFDropDuplicates(self, column, keep='last'):
        self.df = self.df.drop_duplicates(subset=[column], keep=keep)
# ===================================================================================
    ## @brief データフレームを指定列で並び替え
    @MyLogger.deco
    def DFSort(self, column, ascending=True):
        self.df = self.df.sort_values(by=[column], ascending=ascending)
# ===================================================================================
    ## @brief データフレームを指定列と値でフィルタ
    @MyLogger.deco
    def DFFilter(self, column, value, mode='contains'):
        if mode=='contains':
            self.df = self.df[self.df[column].astype(str).str.contains(value)]
        else: #if mode='fullmatch':
            self.df = self.df[self.df[column].astype(str).str.fullmatch(value)]
# ===================================================================================
    ## @brief データフレームに行を追加
    @MyLogger.deco
    def DFAppendRow(self, row):
        # サイズが一致しない場合、仮の列名を追加
        while len(row) > len(self.columns):
            self.DFAppendColumn(['UnknownColumn'+str(len(self.df.columns))])
        # 行追加
        dt = datetime.datetime.now()
        temp = {'timestamp/date':dt.strftime("%Y/%m/%d"),
                'timestamp/time':dt.strftime('%X')}
        for k,v in zip(self.columns, row):
            temp[k] = v
        self.df = self.df.append(temp, ignore_index=True)
        self.rows = list(self.df.index)
# ===================================================================================
    ## @brief データフレームに列を追加
    @MyLogger.deco
    def DFAppendColumn(self, columns, value=''):
        for column in columns:
            if not column in self.df.columns:
                self.df.insert(len(self.df.columns), column, value)
            else:
                MyLogger.warning('column ', column, ' is already exist')
        self.columns = list(self.df.columns)[2:]
# ===================================================================================
    ## @brief 指定列だけ取り出し
    @MyLogger.deco
    def GetListByColumn(self, column):
        return self.df.loc[:,column].values.tolist()
# ===================================================================================
    ## @brief データフレーム列ラベルを取得
    # @note
    # Timestamp用の列を意識しなくていいように削除して渡す。
    @MyLogger.deco
    def GetColumns(self):
        self.columns = list(self.df.columns)[2:]
        return self.columns
# ===================================================================================
    ## @brief データフレーム行indexを取得
    @MyLogger.deco
    def GetRows(self):
        self.rows = list(self.df.index)
        return self.rows
# ===================================================================================
    ## @brief データフレームを辞書型に変換して取得
    @MyLogger.deco
    def GetDict(self):
        return self.df.to_dict('index')
# ===================================================================================
    ## @brief データフレームを文字列型に変換して取得
    # @note
    # データフレームにto_stringというメソッドがあるが、
    # TAB区切りの方が好みなので自作
    @MyLogger.deco
    def GetStr(self):
        ret = ''
        # タイトル行
        isFirstColumn = True
        for column in list(self.df.columns):
            if isFirstColumn:
                ret += column
                isFirstColumn = False
            else:
                ret += '\t' + column
        ret += '\n'
        # データ行
        for row in self.df.to_dict('index').values():
            isFirstColumn = True
            for value in row.values():
                value = str(value)
                if isFirstColumn:
                    ret += value
                    isFirstColumn = False
                else:
                    ret += '\t' + value
            ret += '\n'
        return ret
# ===================================================================================
    ## @brief データフレームをHTML文字列に変換して取得
    @MyLogger.deco
    def GetHTML(self):
        return self.df.to_html(index=False)
# ===================================================================================
    ## @brief Excel更新時のコールバック登録
    @MyLogger.deco
    def AddCallbackOnWrite(self, callback):
        self.OnWriteCallback.append(callback)
# ===================================================================================
    ## @brief Excel更新時のコールバック呼び出し
    @MyLogger.deco
    def OnWrite(self):
        for callback in self.OnWriteCallback:
            callback()
# ===================================================================================
if __name__ == '__main__':
    db = MyDataBase.GetInstance('task.xlsx')
    db.DFAppendColumn(['data/project', 'data/task', 'data/status'])
    db.DFAppendRow(['プロジェクトX','洗濯','OPEN'])
    db.DFAppendRow(['プロジェクトX','家事','DOING'])
    db.DFAppendRow(['プロジェクトY','会議','DONE'])
    db.DFAppendRow(['プロジェクトY','営業','OPEN'])
    MyLogger.success(db.GetColumns())
    MyLogger.success(db.GetDict())
    MyLogger.success(db.GetStr())
    MyLogger.success(db.GetHTML())
    db.DFSort('data/status', ascending=False)
    db.DFDropDuplicates('data/project')
    db.DFWrite()
    input('press any key ...')
# ===================================================================================