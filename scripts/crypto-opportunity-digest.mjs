// Fetches crypto/web3 opportunity announcements from configured public RSS/Atom feeds
// and posts up to ten fresh, relevant items to Telegram. No secrets are logged.
const FEEDS = (process.env.CRYPTO_OPPORTUNITY_FEEDS || [
  "https://blog.gitcoin.co/feed",
  "https://dorahacks.io/blog/rss.xml"
].join("\n")).split(/[\n,]+/).map(x=>x.trim()).filter(Boolean);
const TOKEN=process.env.TELEGRAM_BOT_TOKEN;
const CHAT=process.env.TELEGRAM_CHANNEL_ID;
const LIMIT=Math.min(10,Math.max(1,Number(process.env.DAILY_POST_LIMIT||10)));
if(!TOKEN||!CHAT) throw new Error("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID secrets.");

const htmlDecode=s=>s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,"$1").replace(/<[^>]+>/g," ").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/\s+/g," ").trim();
function items(xml,feed){
 const blocks=[...xml.matchAll(/<(item|entry)\b[\s\S]*?<\/\1>/gi)].map(m=>m[0]);
 return blocks.map(b=>{
   const get=(tag)=>{const m=b.match(new RegExp("<"+tag+"\\b[^>]*>([\\s\\S]*?)<\\/"+tag+">","i"));return m?htmlDecode(m[1]):""};
   const link=b.match(/<link\b[^>]*href=["']([^"']+)["'][^>]*\/?\s*>/i);
   const url=get("link")|| (link?link[1]:"");
   return {title:get("title"),url,description:get("description")||get("summary")||get("content"),date:get("pubDate")||get("published")||get("updated"),feed};
 }).filter(x=>x.title&&/^https?:\/\//i.test(x.url));
}
const matchTerms=/\b(bount(y|ies)|grant(s)?|hackathon|prize(s)?|reward(s)?|paid|earn|funding|stipend|contest|bug bounty)\b/i;
const cryptoTerms=/\b(crypto|web3|blockchain|ethereum|solana|bitcoin|defi|dao|token|on.?chain|wallet|protocol|smart contract)\b/i;
const cutoff=Date.now()-14*864e5;
const found=[];
for(const feed of FEEDS){
 try{
  const res=await fetch(feed,{headers:{"user-agent":"DFRE-CryptoDigest/1.0"},signal:AbortSignal.timeout(20000});
  if(!res.ok) throw new Error("HTTP "+res.status);
  const xml=await res.text();
  for(const item of items(xml,feed)){
   if(!matchTerms.test(item.title+" "+item.description)||!cryptoTerms.test(item.title+" "+item.description)) continue;
   const date=Date.parse(item.date||"");
   if(Number.isFinite(date)&&date<cutoff) continue;
   found.push(item);
  }
 }catch(e){console.warn("Feed skipped:",feed,e.message);}
}
const unique=[...new Map(found.map(x=>[x.url,x])).values()].sort((a,b)=>(Date.parse(b.date)||0)-(Date.parse(a.date)||0)).slice(0,LIMIT);
if(!unique.length){console.log("No matching fresh opportunities found; nothing posted.");process.exit(0);}
for(const x of unique){
 const text="🪙 <b>"+escapeHtml(x.title)+"</b>\n"+escapeHtml(x.description.slice(0,450))+"\n\n<a href=\""+escapeAttr(x.url)+"\">Open opportunity / source</a>\n<i>Source: "+escapeHtml(new URL(x.feed).hostname)+"</i>";
 const res=await fetch("https://api.telegram.org/bot"+TOKEN+"/sendMessage",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({chat_id:CHAT,text,parse_mode:"HTML",disable_web_page_preview:true})});
 const data=await res.json();
 if(!res.ok||!data.ok) throw new Error("Telegram send failed: "+(data.description||res.status));
 console.log("Posted:",x.title);
}
console.log("Posted "+unique.length+" item(s).");
function escapeHtml(s){return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function escapeAttr(s){return escapeHtml(s).replace(/"/g,"&quot;");}
