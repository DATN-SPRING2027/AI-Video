from pathlib import Path
import wave, html, json
p=Path(r'F:\LEARN KÌ 8\ĐATN\CreateVideo\studio\zero-mem-sag')
scenes=[
('VẤN ĐỀ','Quyết định cũ đang ở đâu?', 'Một câu hỏi quen thuộc khi hội thoại trở nên rất dài.', ['HỘI THOẠI DÀI','…','QUYẾT ĐỊNH CŨ ?']),
('TRƯỚC • SAG HIỆN TẠI','Lịch sử gần nhất → tóm tắt → prompt','Tải tối đa 200 tin gần nhất; khi vượt ngân sách, chi tiết cũ có thể mất.', ['200 TIN GẦN NHẤT','TÓM TẮT / CẮT BỚT','LLM TRẢ LỜI']),
('Ý TƯỞNG • ZERO-MEM','Giữ nguyên bằng chứng gốc','Tạo hai cách nhìn bổ sung trên lịch sử, không cần LLM để tạo memory.', ['HỘI THOẠI GỐC','GRAPH THỰC THỂ','TRẬT TỰ THỜI GIAN']),
('SAU • LUỒNG ĐỀ XUẤT','Tìm đúng đoạn trước khi trả lời','Graph kết nối thông tin; thời gian giữ thứ tự và ngữ cảnh lân cận.', ['CÂU HỎI','GRAPH + THỜI GIAN','CHỌN BẰNG CHỨNG']),
('VÍ DỤ','Từ câu hỏi đến quyết định','Đoạn gốc được chọn cùng thời điểm và nguồn trước khi đưa vào prompt.', ['“QUYẾT ĐỊNH NÀO?”','TIN NHẮN ĐÃ CHỐT','PROMPT + TÀI LIỆU']),
('TÁC DỤNG','Ngữ cảnh gọn, có thể truy vết','Lợi ích cần được đo trên dữ liệu SAG thực tế.', ['TÌM LẠI THÔNG TIN','DẪN NGUỒN RÕ','GIẢM CONTEXT THỪA']),
('RANH GIỚI AN TOÀN','Kiểm tra quyền trước khi dùng','Nguồn bị thu hồi quyền không được trở lại qua index hoặc cache.', ['DANH TÍNH + PHẠM VI','KIỂM TRA QUYỀN','EVIDENCE ĐƯỢC PHÉP']),
('LỘ TRÌNH','Đo trước khi triển khai','Chạy song song và đánh giá trên bộ kiểm thử mới.', ['01 KIỂM KÊ PR 40','02 BASELINE + CHẠY THỬ','03 ĐÁNH GIÁ → TRIỂN KHAI']),
('KẾT LUẬN','Đúng bằng chứng. Đúng quyền.','PR 40 chưa đạt điều kiện triển khai; đây là hướng đề xuất.', ['CHẤT LƯỢNG','BẢO MẬT','CHI PHÍ + ĐỘ TRỄ'])]
css='''*{box-sizing:border-box}html,body{margin:0;background:#09121d;color:#f4f7fa;font-family:Arial,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden;background:radial-gradient(circle at 80% 10%,#143c49,#09121d 58%)}.scene{position:absolute;inset:0}.inner{position:absolute;inset:0;padding:84px 110px}.eyebrow{color:#6ee7cf;font-size:23px;font-weight:700;letter-spacing:3px}.heading{font-size:64px;line-height:1.12;max-width:1500px;margin:30px 0 20px}.sub{font-size:28px;color:#c4d4df;max-width:1500px;line-height:1.45}.flow{display:flex;align-items:center;gap:24px;margin-top:100px}.box{width:480px;min-height:215px;padding:34px;border:2px solid #386274;border-radius:22px;background:#112b39;display:flex;align-items:center;justify-content:center;text-align:center;font-size:31px;font-weight:700;line-height:1.25}.box:nth-child(3){border-color:#57d1bc;background:#124e50}.arrow{font-size:48px;color:#6ee7cf}.footer{position:absolute;bottom:55px;left:110px;color:#a8bac5;font-size:21px}.counter{position:absolute;right:110px;bottom:55px;color:#80a8b4;font-size:22px}'''
starts=[]; t=0
for i in range(1,10):
 with wave.open(str(p/'assets'/f'voice-{i}.wav')) as w: duration=w.getnframes()/w.getframerate()
 d=round(max(duration+1.1,6),3);starts.append((round(t,3),d));t+=d
parts=[];anim=[];audio=[]
for i,((tag,title,sub,boxes),(start,dur)) in enumerate(zip(scenes,starts),1):
 flow=''.join((f'<div class="box b{i}">{html.escape(v)}</div>'+(('<div class="arrow">+</div>' if i==3 and j==1 else '<div class="arrow">→</div>') if j<2 else '')) for j,v in enumerate(boxes))
 parts.append(f'<section id="scene{i}" class="scene clip" data-start="{start}" data-duration="{dur}" data-track-index="1"><div class="inner"><div class="eyebrow">{tag}</div><h1 class="heading">{title}</h1><p class="sub">{sub}</p><div class="flow">{flow}</div><div class="footer">ZERO-MEM × SAG  /  Minh hoạ kiến trúc đề xuất</div><div class="counter">{i:02} / 09</div></div></section>')
 anim.append(f'tl.fromTo("#scene{i} .inner",{{opacity:0,y:25}},{{opacity:1,y:0,duration:.55,ease:"power3.out"}},{start}); tl.fromTo(".b{i}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,stagger:.3,ease:"power2.out"}},{start+0.5});')
 audio.append(f'<audio id="voice{i}" class="clip" src="assets/voice-{i}.wav" data-start="{start+0.3}" data-duration="{dur-0.3}" data-track-index="2"></audio>')
doc=f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>{css}</style><script src="assets/gsap.min.js"></script></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="{t:.3f}" data-width="1920" data-height="1080">{''.join(parts)}{''.join(audio)}</div><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}window.__timelines["main"]=tl;</script></body></html>'''
(p/'index.html').write_text(doc,encoding='utf-8')
(p/'timings.json').write_text(json.dumps(starts,indent=2),encoding='utf-8')
print(f'Duration: {t:.1f}s')
