export interface User { id:number; email:string; name:string; role:'student'|'tutor'|'admin'; is_verified:boolean; is_active:boolean }
export interface Course { id:number; name:string; academic_year:string; level:number; invite_code:string; tutor_id:number|null; tutor?:User; is_active:boolean }
export interface Item { id:number; aspect_id:number; text:string; order:number; reverse_scored:boolean; help_text:string }
export interface Aspect { id:number; level:number; name:string; description:string; order:number; low_max:number; medium_max:number; messages:Record<string,string>; items:Item[] }
export interface Result { aspect_id:number; aspect:string; average:number; level:string; message:string }
export interface Attempt { id:number; created_at:string; student:User; course:Course; encouragement:string; results:Result[] }

