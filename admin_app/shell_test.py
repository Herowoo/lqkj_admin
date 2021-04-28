import os

os.chdir('/home/admin/lqkj_admin/SVN/项目外来文件/合同评审单')
# os.system('/home/admin/lqkj_admin/SVN')
os.system('svn up')
res=os.popen('svn status')
for item in res:
    uri=item.replace('?','').strip()
    os.system('svn add %s'%uri)
os.system("svn ci -m 'OASystem Add'")
# os.system('ls')
# os.system('svn up')
# os.system('svn add 文件上传测试.txt')
# os.system("svn ci -m '文件上传测试.txt'")