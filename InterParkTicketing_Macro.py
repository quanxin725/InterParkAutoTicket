import time
import easyocr
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from enum import Enum

class SeatType(Enum):
    TABLE_SEAT = 1
    VIP_SEAT = 2
    R_SEAT = 3
    S_SEAT = 4
    A_SEAT = 5

def launch_browser():
    # 防止浏览器关闭的选项
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    # 创建Chrome驱动
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def login(driver, id, password):
    # 等待页面加载完成
    driver.implicitly_wait(3)

    # 访问网站
    driver.get(url='https://ticket.interpark.com/Gate/TPLogin.asp')

    # 修复错误
    # 所需信息位于Iframe中（与整体框架分开）
    # 将driver切换到Iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframes[0])

    # 输入ID
    id_input = driver.find_element(By.CSS_SELECTOR, '#userId')
    id_input.send_keys(id)
    time.sleep(1)
    # 输入密码
    pw_input = driver.find_element(By.CSS_SELECTOR, '#userPwd')
    pw_input.send_keys(password)
    time.sleep(1)
    # 点击按钮
    button = driver.find_element(By.CSS_SELECTOR, '#btn_login')
    button.click()
    time.sleep(1)


def access_performance_page(driver, my_Url):
    driver.get(my_Url)
    time.sleep(0.3)

    button = driver.find_element(By.XPATH, "//*[@id='popup-prdGuide']/div/div[3]/button")
    button.click()
    time.sleep(1)


def select_date(driver, my_WantDay):
    find_day = driver.find_element(By.XPATH, "//li[text()='" + str(my_WantDay) + "']")
    find_day.click()


def proceed_to_reservation(driver):
    # 点击预订按钮
    go_button = driver.find_element(By.CSS_SELECTOR, "a.sideBtn.is-primary")
    go_button.click()

    # 最长等待10秒直到弹窗出现
    wait = WebDriverWait(driver, 10)
    wait.until(EC.number_of_windows_to_be(2))  # 设置期望的窗口数量，本例应为2个

    # 获取所有窗口句柄
    window_handles = driver.window_handles

    # 获取当前窗口句柄
    current_window_handle = driver.current_window_handle
    print(driver.current_window_handle)

    # 查找新打开的窗口句柄
    new_window_handle = None
    for handle in window_handles:
        if handle != current_window_handle:
            new_window_handle = handle
            break

    # 切换到新打开的窗口
    if new_window_handle:
        driver.switch_to.window(new_window_handle)
    else:
        print("새로운 창이 열리지 않았습니다.")


# 查找并选择座位
def select_seat(driver, seat_type, start_li_num=1, search_count=0):
    print(driver.window_handles)
    print(driver.current_window_handle)
    driver.switch_to.window(driver.window_handles[-1])
    driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))

    # 选择座位等级
    seat_xpath = {
        SeatType.TABLE_SEAT: '//*[@id="GradeRow"][2]/td[1]/div/span[2]',
        SeatType.VIP_SEAT: '//*[@id="GradeRow"][3]/td[1]/div/span[2]',
        SeatType.R_SEAT: '//*[@id="GradeRow"][4]/td[1]/div/span[2]',
        SeatType.S_SEAT: '//*[@id="GradeRow"][5]/td[1]/div/span[2]',
        SeatType.A_SEAT: '//*[@id="GradeRow"][6]/td[1]/div/span[2]'
    }
    seat_xpath_value = seat_xpath.get(seat_type)
    if seat_xpath_value:
        driver.find_element(By.XPATH, seat_xpath_value).click()
    else:
        print("Invalid seat type")

    li_elements = driver.find_elements(By.XPATH, '//*[@id="GradeDetail"]/div/ul/li')
    li_maxcount = len(li_elements)
    li_num = start_li_num
    
    while True:
        # 优先查找非零座位
        elements = driver.find_elements(By.XPATH, '//*[@id="GradeDetail"]/div/ul/li')
        for idx, element in enumerate(elements, start=1):
            text = element.text
            if "0석" not in text:
                print(f'{idx}번째 좌석은 0석 아니다.')
                li_num = idx
                search_count += 1
                if search_count >= 5:  # 第5次搜索时刷新
                    driver.refresh()  # 刷新浏览器
                    select_seat(driver, seat_type, li_num, 0)  # 重新开始
                    return
                
        # 选择具体区域
        if li_num > li_maxcount:
            li_num = 1

        driver.find_element(By.XPATH, f'//*[@id="GradeDetail"]/div/ul/li[{li_num}]/a').click()

        # 进入座位选择iframe
        driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeatDetail"]'))

        # 如果有座位则选择
        try:
            driver.find_element(By.XPATH, '//*[@id="Seats"]').click()
            # 执行支付函数
            payment(driver)
            print('select payment')
            break

        # 如果没有座位则重新搜索
        except:
            print(f'******{li_num}번째 영역에는 자리가 없습니당. 다시 선택합니다*******')
            li_num = li_num + 1
            driver.switch_to.default_content()
            driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))
            driver.find_element(By.XPATH, '/html/body/form[1]/div/div[1]/div[3]/div/p/a/img').click()
            time.sleep(0.5)           

            if li_num % 2 == 0:  # 如果 li_num 是 2 的倍数
                driver.refresh()  # 刷新浏览器
                print(f'******새로고침*******')
                select_seat(driver, seat_type, li_num)
                break


# 显示弹窗函数
def show_popup():
    root = tk.Tk()
    root.withdraw()  # 不显示窗口
    messagebox.showinfo("결제해주세요!!", "자리를 성공적으로 잡았습니다 후딱 결제해주세요!!")
    root.mainloop()

# 支付
def payment(driver):
    # 点击完成座位选择
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmSeat"]'))
    driver.find_element(By.XPATH, '//*[@id="NextStepImage"]').click()

    # 选择价格
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmBookStep']"))
    select = Select(driver.find_element(By.XPATH, '//*[@id="PriceRow001"]/td[3]/select'))
    select.select_by_index(1)
    driver.switch_to.default_content()
    driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # 确认预订者
    driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmBookStep']"))
    driver.find_element(By.XPATH, '//*[@id="YYMMDD"]').send_keys('951207')
    driver.switch_to.default_content()
    driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # 显示预订完成信息
    show_popup()

    while True:
        time.sleep(3600)  # 等待2小时

    # # 选择支付方式
    # driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmBookStep"]'))
    # driver.find_element(By.XPATH, '//*[@id="Payment_22004"]/td/input').click()

    # select2 = Select(driver.find_element(By.XPATH, '//*[@id="BankCode"]'))
    # select2.select_by_index(1)
    # driver.switch_to.default_content()
    # driver.find_element(By.XPATH, '//*[@id="SmallNextBtnImage"]').click()

    # # 同意后支付
    # driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="ifrmBookStep"]'))
    # driver.find_element(By.XPATH, '//*[@id="checkAll"]').click()
    # driver.switch_to.default_content()
    # driver.find_element(By.XPATH, '//*[@id="LargeNextBtnImage"]').click()

# 解除安全验证
def ocr_captcha(driver, my_SeatType):
    # 将当前窗口切换到Interpark页面
    driver.switch_to.window(driver.window_handles[1])
    
    # 跳转到iframe
    while True:
        try:
            # 跳转到iframe
            driver.switch_to.frame(driver.find_element(By.XPATH, "//*[@id='ifrmSeat']"))
            break  # 找到iframe后结束循环
        except NoSuchElementException:
            print("이미지가 없어서 재검색중입니다....")
            time.sleep(3)  # 等待3秒后重试


    # 截图后进行验证
    while True:
            # 等待验证码图片出现
            capchaPng = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//*[@id='imgCaptcha']")))

            # 指定easyocr识别的语言
            reader = easyocr.Reader(['en'])

            # 识别截图中的字符串
            result = reader.readtext(capchaPng.screenshot_as_png, detail=0)

            # 由于图像包含点和直线，识别不完全，因此手动修正数据
            capchaValue = result[0].replace(' ', '').replace('5', 'S').replace('0', 'O').replace('$', 'S').replace(',', '')\
                .replace(':', '').replace('.', '').replace('+', 'T').replace("'", '').replace('`', '')\
                .replace('1', 'L').replace('e', 'Q').replace('3', 'S').replace('€', 'C').replace('{', '').replace('-', '')

            # 点击输入文本框
            element = driver.find_element(By.XPATH, "//*[@id='divRecaptcha']/div[1]/div[3]")
            # 点击元素
            element.click()
            
            # 将识别的字符串输入文本框
            chapchaText = driver.find_element(By.XPATH, '//*[@id="txtCaptcha"]')
            chapchaText.send_keys(capchaValue)
            chapchaText.send_keys(Keys.ENTER)
            
            # 检查验证码元素是否存在
            captcha_element = driver.find_element(By.XPATH, '//*[@id="divRecaptcha"]')

            # 检查验证码元素是否显示
            if captcha_element.is_disStartTicketingMacroed():
                # 验证码输入失败时重试
                print('Captcha entered incorrectly, retrying...')
                driver.find_element(By.XPATH, '//*[@id="divRecaptcha"]/div[1]/div[1]/a[1]').click()
            else:
                # 验证码输入成功时
                print('Captcha entered successfully')
                select_seat(driver, my_SeatType)
                break

def StartTicketingMacro():

    # 购票链接
    my_Url = "https://tickets.interpark.com/goods/24005132"  
    # 用户名
    my_Id = "아이디를 입력하는 곳"
    # 密码
    my_PassWord = "비밀번호를 입력하는 곳"  
    # 座位
    my_SeatType = SeatType.R_SEAT
    # 日期
    my_WantDay = 25

    # 登录
    driver = launch_browser()

    login(driver, my_Id, my_PassWord)       # 登录
    access_performance_page(driver, my_Url) # 关闭页面错误弹窗
    select_date(driver, my_WantDay)         # 选择日期
    proceed_to_reservation(driver)          # 预订
    ocr_captcha(driver, my_SeatType)        # 验证码







#################################以后######################################################

def Button_Click():
    id_text = id_entry.get()
    password_text = password_entry.get()
    performance_text = performance_value.get()
    birthday_text = birthday_entry.get()
    option_text = option_var.get()
    
    StartTicketingMacro()






def add_log(log_message):
    log_text.config(state=tk.NORMAL)  # 将日志设为可编辑
    log_text.insert(tk.END, log_message + "\n")
    log_text.config(state=tk.DISABLED)  # 将日志设为只读
    log_text.see(tk.END)  # 将日志窗口滚动到底部
    with open("log.txt", "a") as log_file:
        log_file.write(log_message + "\n")

def create_label_entry(window, text, row):
    label = tk.Label(window, text=text, width=12, anchor="center")  # 居中
    label.grid(row=row, column=0)
    entry = tk.Entry(window)
    entry.grid(row=row, column=1, columnspan=5, pady=5, sticky="ew")  # 将文本框居中
    return entry

def create_button(window, text, row):
    button = tk.Button(window, text=text, command=Button_Click)
    button.grid(row=row, column=0, columnspan=6, pady=10)

def create_booking_window():
    # 创建Tkinter窗口
    window = tk.Tk()
    window.title("인터파크 예약 매크로")

    # 设置窗口大小
    window.geometry("400x400")

    global birthday_entry, id_entry, password_entry, performance_value, option_var, log_text

    # 输入生日
    birthday_entry = create_label_entry(window, "생년월일:", 0)

    # 输入用户名
    id_entry = create_label_entry(window, "아이디:", 1)

    # 输入密码
    password_entry = create_label_entry(window, "비밀번호:", 2)

    # 输入商品名（公演编号）
    performance_value = create_label_entry(window, "상품명(공연번호):", 3)

    # 添加选项
    option_var = tk.StringVar(value="")  # 初始化
    option_label = tk.Label(window, text="선택지:", width=12, anchor="center")  # 居中
    option_label.grid(row=4, column=0)
    options = ["테이블석", "VIP석", "R석", "S석", "A석"]
    for i, option in enumerate(options):
        tk.Radiobutton(window, text=option, variable=option_var, value="").grid(row=4, column=i+1, padx=1)


    # 添加用于显示日志的文本框
    log_text = tk.Text(window, height=10, width=50, state=tk.DISABLED, bg="light gray")  # 设置为只读，浅灰背景
    log_text.grid(row=6, column=0, columnspan=6, pady=10)

    # 打开日志文件读取之前的记录
    try:
        with open("log.txt", "r") as log_file:
            log_text.insert(tk.END, log_file.read())
    except FileNotFoundError:
        pass

    # 添加按钮
    create_button(window, "Send Keys", 5)

    # 运行窗口
    window.mainloop()

if __name__ == "__main__":
    StartTicketingMacro()
    #create_booking_window()



