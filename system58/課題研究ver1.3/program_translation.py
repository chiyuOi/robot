import asyncio

# =========================
# グローバル状態
# =========================
list_cord = []
block_stack = []
field = 0
REG = None


# run が見つかったらここに入る
last_command = None

# =========================
# 演算子
# =========================
async def OPERATOR(op, a, b):
    a = float(a)
    b = float(b)

    if op == "<":
        return a < b
    if op == ">":
        return a > b
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    return False

# =========================
# コマンド
# =========================
async def CMD_PRINT():
    global field
    print(list_cord[field + 1])
    field += 2

async def CMD_SLEEP():
    global field
    t = float(list_cord[field + 1])
    field += 2
    await asyncio.sleep(t)

async def CMD_SEARCH():
    global field, REG

    source = list_cord[field + 1]   # voice / camera
    key    = list_cord[field + 2]   # text / tip / hand_sign etc

    # 仮：state を辞書っぽく見る
    try:
        REG = getattr(getattr(state, source), key)#main接続しないとないやつ
    except Exception:
        REG = None

    field += 3

async def CMD_RUN():
    global field, REG

    motion = list_cord[field + 1]

    # REG があれば tip に使う
    if REG is not None:
        return {
            "type": motion,
            "tip": REG
        }
    else:
        return {
            "type": motion
        }

    field += 2

async def CMD_IF():
    global field

    op = list_cord[field + 1]
    a  = list_cord[field + 2]
    b  = list_cord[field + 3]

    result = await OPERATOR(op, a, b)
    field += 4

    if result:
        return
    else:
        await SKIP_BLOCK()

async def CMD_WHILE():
    global field

    cond_pos = field
    op = list_cord[field + 1]
    a  = list_cord[field + 2]
    b  = list_cord[field + 3]

    field += 4
    body_start = field

    while await OPERATOR(op, a, b):
        field = body_start
        while list_cord[field] != "end":
            await EXEC()

    await SKIP_BLOCK()

async def CMD_END():
    global field
    field += 1

# =========================
# ブロックスキップ
# =========================
async def SKIP_BLOCK():
    global field
    depth = 1

    field += 1  # if / while の次から見る

    while field < len(list_cord) and depth > 0:
        token = list_cord[field]

        if token in ("if", "while"):
            depth += 1
        elif token == "end":
            depth -= 1

        field += 1

# =========================
# 実行ディスパッチ
# =========================
async def EXEC():
    global field
    token = list_cord[field]
    """
    ==============================================================================================================================================================
    関数名これ
    """

    if token == "print":
        await CMD_PRINT()
    elif token == "if":
        await CMD_IF()
    elif token == "while":
        await CMD_WHILE()
    elif token == "search":
        await CMD_SEARCH()
    elif token == "run":
        return await CMD_RUN()
    elif token == "sleep":
        await CMD_SLEEP()
    elif token == "end":
        field += 1
    else:
        field += 1
    # ==========================================
    # 自作スクリプト言語：トークン仕様
    # ==========================================
    #
    # すべて「空白区切り」
    # 上から順に 1 トークンずつ実行される
    #　<>はいらない、説明時につけてる
    #　
    # ------------------------------------------
    # print <value>
    #   ・次の1要素を表示する
    #
    # if <op> <a> <b>
    #   ・条件分岐
    #   ・op : < > == !=
    #   ・a, b : 即値（現状は数値 or 文字）
    #   ・条件が false の場合、対応する end までスキップ
    #
    # while <op> <a> <b>
    #   ・条件ループ
    #   ・if と同じ比較ルール
    #
    # end
    #   ・if / while ブロックの終了
    #   ・ネスト可能
    #
    # ------------------------------------------
    # search <source> <key>
    #   ・state から値を取得
    #   ・取得結果は一時レジスタ REG に保存
    #
    #   source 例:
    #     camera / voice / face
    #
    #   key 例:
    #     camera : tip / hand_sign
    #     voice  : text / intent
    #
    # ------------------------------------------
    # run <motion>
    #   ・brain に渡す行動コマンドを生成
    #   ・REG が存在する場合、tip として利用
    #
    #   例:
    #     run tracking
    #
    # ------------------------------------------
    # sleep <seconds>
    #   ・非同期で指定秒数待機
    #   ・float 対応
    #
    # ------------------------------------------
    # 実行モデル
    #   ・逐次実行
    #   ・if / while はブロック構造
    #   ・変数は未実装（REGのみ）
    #
    # ==========================================


# =========================
# メイン実行
# =========================
def syntax_check(tokens):
    depth = 0
    i = 0
    n = len(tokens)

    while i < n:
        t = tokens[i]

        if t in ("if", "while"):
            # if < a b
            if i + 3 >= n:
                return False, f"{t} needs 3 arguments"
            depth += 1
            i += 4

        elif t == "end":
            depth -= 1
            if depth < 0:
                return False, "unexpected end"
            i += 1

        elif t in ("print", "sleep", "run"):
            if i + 1 >= n:
                return False, f"{t} needs argument"
            i += 2

        else:
            i += 1

    if depth != 0:
        return False, "missing end"

    return True, None

async def run_cord():
    global field, last_command
    while field < len(list_cord) and last_command is None:
        await EXEC()
    return last_command

# =========================
# テスト用
# =========================
if __name__ == "__main__":
    # GUI側ではここを置き換える
    code = input("enter cord: ")

    list_cord = code.split()
    field = 0
    last_command = None

    cmd = asyncio.run(run_cord())
    print("result:", cmd)
