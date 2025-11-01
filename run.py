import os
import time
from utils.browser import Browser
from utils.captcha import get_captcha_code
from config import ACCOUNT, ALIVE_SECOND, INTERVAL_MINUTE,PASSWORD,PROXY,USER_AGENT
from nb_log import get_logger
logger = get_logger(__name__)


def key_alive(page):
    # 默认打开第一台云电脑
    if page.ele(".desktopcom-enter", timeout=10):
        logger.info("打开云电脑界面成功！")
        page.ele(".desktopcom-enter").click()
        page.wait(ALIVE_SECOND)
        logger.info("保活成功！")
        return True
    else:
        logger.error("打开云电脑界面失败！")
        return False

def login(page, account,proxy):
    if page.ele(".code", timeout=10):
        logger.info("检测到验证码！")
        code= get_captcha_code(account,proxy)
        page.ele(".code").input(code)
    page.listen.start('desk.ctyun.cn:8810/api/auth/client/login') 
    page.ele(".el-button el-button--primary btn-submit btn-submit-pc").click()
    response = page.listen.wait(timeout=5)
    login_info = response._raw_body
    logger.info(f"登录信息: {response._raw_body}")

    if "云电脑租户" in login_info:
        logger.info("登录成功！")
    elif "验证码错误" in login_info:
        logger.error("验证码错误！")
        return False
    elif "图形验证码错误" in login_info:
        logger.error("图形验证码错误")
        return False
    else:
        logger.error("登录失败！")
        return False
    
    return key_alive(page)

def main():
    account = ACCOUNT
    password = PASSWORD
    proxy = PROXY
    user_agent = USER_AGENT


    browser = Browser(proxy_server=proxy,user_agent=user_agent,data_path=os.path.join(os.getcwd(), "data"))
    page = browser.get_page()
    page.get("https://pc.ctyun.cn")

    if page.ele(".desktopcom-enter", timeout=10):
        logger.info("已成功登陆！")
        key_alive(page)
    elif page.ele(".account", timeout=10):
        logger.info("页面打开成功！")
        page.ele(".account").click()
        page.ele(".account").input(account)
        page.ele(".password").input(password)
        for i in range(3):
            if login(page, account,proxy):
                break
    browser.quit()


if __name__ == "__main__":
    import schedule

    def job(retry=3):
        if retry <= 0:
            logger.error("保活任务运行失败！")
            return
        logger.info(f"开始保活任务，剩余重试次数: {retry}")
        try:
            main()
        except Exception as e:
            logger.exception(f"保活任务运行失败: {e}，剩余重试次数: {retry}")
            job(retry-1)
    # 每45分钟运行一次
    schedule.every(INTERVAL_MINUTE).minutes.do(job)
    # 立即运行一次
    job()
    while True:
        schedule.run_pending()
        time.sleep(1)
